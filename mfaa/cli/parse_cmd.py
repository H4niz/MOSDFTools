"""
Parse Command
=============

Parse collected FSEvents files.
"""

import click
import json
from pathlib import Path
from datetime import datetime
from mfaa.parser.fsevents_parser import FSEventsParser
from mfaa.parser.xattr_parser import XattrParser


@click.command(name='parse')
@click.argument(
    'input_path',
    type=click.Path(exists=True, resolve_path=True)
)
@click.option(
    '--output', '-o',
    type=click.Path(dir_okay=False, resolve_path=True),
    required=True,
    help='Output JSON file for parsed events'
)
@click.option(
    '--xattr',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help='Path to xattr records JSON file'
)
@click.option(
    '--format',
    type=click.Choice(['json', 'json-compact'], case_sensitive=False),
    default='json',
    help='Output format (default: json)'
)
@click.pass_context
def parse(ctx, input_path, output, xattr, format):
    """
    Parse FSEvents database files.

    Parses both FSEvents v1 and v2 formats, including gzip-compressed files.
    Outputs structured JSON with all event details.

    \b
    Arguments:
        INPUT_PATH  Directory containing FSEvents files or single file

    \b
    Examples:
        # Parse collected FSEvents
        mfaa parse ./artifacts/fsevents --output events.json

        # Parse with xattr data
        mfaa parse ./fsevents --output events.json --xattr xattr.json

        # Compact output
        mfaa parse ./fsevents --output events.json --format json-compact

    \b
    Output Format:
        JSON with keys: events, metadata, statistics
    """
    verbose = ctx.obj.get('verbose', False)

    click.echo(click.style("mFAA FSEvents Parser", fg='cyan', bold=True))
    click.echo("=" * 50)

    input_path = Path(input_path)

    # Step 1: Parse FSEvents
    click.echo(f"\n📂 Input: {input_path}")

    parser = FSEventsParser()
    events = []

    if input_path.is_file():
        # Single file
        click.echo("Parsing single file...")
        with click.progressbar(length=1, label='Parsing', show_eta=False) as bar:
            events = parser.parse_file(input_path)
            bar.update(1)
    else:
        # Directory
        click.echo("Parsing directory...")
        files = list(input_path.glob('*'))
        fsevents_files = [f for f in files if f.is_file() and not f.name.startswith('.')]

        if not fsevents_files:
            click.echo(click.style("❌ No FSEvents files found!", fg='red'))
            return

        click.echo(f"Found {len(fsevents_files)} files")

        with click.progressbar(
            fsevents_files,
            label='Parsing files',
            show_eta=True
        ) as bar:
            for file_path in bar:
                try:
                    file_events = parser.parse_file(file_path)
                    events.extend(file_events)
                except Exception as e:
                    if verbose:
                        click.echo(f"\n  ⚠️  Failed to parse {file_path.name}: {e}")

    if not events:
        click.echo(click.style("❌ No events parsed!", fg='red'))
        return

    click.echo(click.style(f"✓ Parsed {len(events)} events", fg='green'))

    # Step 2: Parse xattr if provided
    xattr_records = {}
    if xattr:
        click.echo(f"\n🏷️  Loading xattr records from: {Path(xattr).name}")
        xattr_parser = XattrParser()

        try:
            with open(xattr, 'r') as f:
                xattr_data = json.load(f)

            for record_data in xattr_data:
                path = Path(record_data['file_path'])
                # Parse the record (simplified - would need full XattrRecord reconstruction)
                xattr_records[path] = record_data

            click.echo(click.style(f"✓ Loaded {len(xattr_records)} xattr records", fg='green'))
        except Exception as e:
            click.echo(click.style(f"⚠️  Failed to load xattr: {e}", fg='yellow'))

    # Step 3: Build output structure
    click.echo(f"\n💾 Writing output to: {Path(output).name}")

    # Calculate statistics
    from collections import Counter
    event_types_count = Counter()
    for event in events:
        for et in event.event_types:
            event_types_count[et.value] += 1

    timestamps = [e.timestamp for e in events]
    earliest = min(timestamps) if timestamps else None
    latest = max(timestamps) if timestamps else None

    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'parser_version': '1.0.0',
            'source': str(input_path),
            'total_events': len(events)
        },
        'statistics': {
            'total_events': len(events),
            'event_types': dict(event_types_count),
            'time_range': {
                'earliest': earliest.isoformat() if earliest else None,
                'latest': latest.isoformat() if latest else None
            }
        },
        'events': [
            {
                'event_id': e.event_id,
                'timestamp': e.timestamp.isoformat(),
                'path': str(e.path),
                'event_types': [et.value for et in e.event_types],
                'flags': e.flags.value,
                'node_id': e.node_id
            }
            for e in events
        ]
    }

    # Add xattr if available
    if xattr_records:
        output_data['xattr_records'] = xattr_records

    # Write output
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        if format == 'json-compact':
            json.dump(output_data, f)
        else:
            json.dump(output_data, f, indent=2)

    # Summary
    click.echo(click.style("✓ Parsing complete!", fg='green'))

    if verbose:
        click.echo("\nStatistics:")
        click.echo(f"  Total events: {len(events)}")
        click.echo(f"  Time range: {earliest} - {latest}" if earliest else "  No events")
        click.echo(f"  Event types: {len(event_types_count)}")

    click.echo(f"\nOutput saved to: {output_path}")
    click.echo("\nNext steps:")
    click.echo(f"  Analyze: mfaa analyze {output_path} --output reports/")
    click.echo(f"  Report: mfaa report {output_path} --format html")
