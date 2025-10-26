"""
Report Command
==============

Generate reports from timeline data.
"""

import click
import json
from pathlib import Path
from datetime import datetime
from mfaa.reporter import CSVReporter, JSONReporter, HTMLReporter
from mfaa.models import Timeline, TimelineEntry, FSEvent, EventFlags, Pattern


@click.command(name='report')
@click.argument(
    'timeline_file',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--format', '-f',
    type=click.Choice(['csv', 'json', 'html', 'executive', 'all'], case_sensitive=False),
    default='html',
    help='Report format (default: html)'
)
@click.option(
    '--output', '-o',
    type=click.Path(resolve_path=True),
    required=True,
    help='Output file or directory'
)
@click.option(
    '--theme',
    type=click.Choice(['light', 'dark'], case_sensitive=False),
    default='light',
    help='HTML theme (default: light)'
)
@click.option(
    '--open-browser',
    is_flag=True,
    help='Open HTML report in browser'
)
@click.option(
    '--min-priority',
    type=int,
    default=0,
    help='Minimum priority score for summary (0-100)'
)
@click.pass_context
def report(ctx, timeline_file, format, output, theme, open_browser, min_priority):
    """
    Generate reports from timeline JSON.

    Takes a timeline JSON file (from analyze or parse command) and generates
    formatted reports in CSV, JSON, or HTML with interactive visualizations.

    \b
    Arguments:
        TIMELINE_FILE  Input timeline JSON file

    \b
    Examples:
        # HTML report with visualizations
        mfaa report timeline.json --format html --output report.html

        # Executive summary
        mfaa report timeline.json --format executive --output summary.html

        # CSV for analysis tools
        mfaa report timeline.json --format csv --output data.csv

        # All formats
        mfaa report timeline.json --format all --output ./reports/

        # High-priority only
        mfaa report timeline.json --format html --output report.html --min-priority 70

    \b
    Formats:
        csv        - CSV files (events, patterns, statistics)
        json       - Structured JSON
        html       - Interactive HTML with charts and timeline
        executive  - Executive summary HTML
        all        - Generate all formats
    """
    verbose = ctx.obj.get('verbose', False)

    click.echo(click.style("mFAA Report Generator", fg='cyan', bold=True))
    click.echo("=" * 50)

    # Load timeline data
    click.echo(f"\n📂 Loading: {Path(timeline_file).name}")

    try:
        with open(timeline_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        click.echo(click.style(f"❌ Failed to load timeline: {e}", fg='red'))
        return

    # Reconstruct timeline
    click.echo("Reconstructing timeline...")

    try:
        # Reconstruct events
        events = []
        for event_data in data.get('events', []):
            event = FSEvent(
                event_id=event_data['event_id'],
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                path=Path(event_data['path']),
                flags=EventFlags(event_data['flags']),
                node_id=event_data['node_id']
            )
            events.append(event)

        # Create timeline entries (simplified - real version would include scoring)
        from mfaa.analyzer.priority_scorer import PriorityScorer

        scorer = PriorityScorer()
        entries = []

        with click.progressbar(events, label='Scoring events', show_eta=False) as bar:
            for event in bar:
                score = scorer.calculate_score(event)
                category = scorer.categorize_score(score)

                entry = TimelineEntry(
                    event=event,
                    priority_score=score,
                    priority_category=category
                )
                entries.append(entry)

        # Reconstruct patterns if available
        patterns = []
        for pattern_data in data.get('patterns', []):
            pattern = Pattern(
                pattern_type=pattern_data['pattern_type'],
                severity=pattern_data['severity'],
                start_time=datetime.fromisoformat(pattern_data['start_time']),
                end_time=datetime.fromisoformat(pattern_data['end_time']),
                event_count=pattern_data['event_count'],
                affected_paths=[Path(p) for p in pattern_data.get('affected_paths', [])],
                description=pattern_data['description'],
                indicators=pattern_data.get('indicators', {})
            )
            patterns.append(pattern)

        # Create timeline
        timeline = Timeline(
            entries=entries,
            patterns=patterns,
            statistics=data.get('statistics', {}),
            info=data.get('metadata', {})
        )

        click.echo(click.style(f"✓ Loaded {len(entries)} events, {len(patterns)} patterns", fg='green'))

    except Exception as e:
        click.echo(click.style(f"❌ Failed to reconstruct timeline: {e}", fg='red'))
        if verbose:
            import traceback
            traceback.print_exc()
        return

    # Apply priority filter if specified
    if min_priority > 0:
        original_count = len(timeline.entries)
        timeline.entries = [e for e in timeline.entries if e.priority_score >= min_priority]
        click.echo(f"Filtered to {len(timeline.entries)} events (min priority: {min_priority})")

    # Generate reports
    click.echo("\n📄 Generating Reports...")

    output_path = Path(output)

    formats_to_generate = []
    if format == 'all':
        formats_to_generate = ['csv', 'json', 'html', 'executive']
        # For 'all', output should be a directory
        if not output_path.suffix:
            output_path.mkdir(parents=True, exist_ok=True)
    else:
        formats_to_generate = [format]

    try:
        for fmt in formats_to_generate:
            if fmt == 'csv':
                file_path = output_path if output_path.suffix == '.csv' else output_path / 'report.csv'
                file_path.parent.mkdir(parents=True, exist_ok=True)

                reporter = CSVReporter()
                reporter.generate(timeline, file_path, include_patterns=True, include_statistics=True)
                click.echo(click.style(f"  ✓ CSV: {file_path.name}", fg='green'))

            elif fmt == 'json':
                file_path = output_path if output_path.suffix == '.json' else output_path / 'report.json'
                file_path.parent.mkdir(parents=True, exist_ok=True)

                reporter = JSONReporter()
                reporter.generate(timeline, file_path, pretty=True)
                click.echo(click.style(f"  ✓ JSON: {file_path.name}", fg='green'))

            elif fmt == 'html':
                file_path = output_path if output_path.suffix == '.html' else output_path / 'report.html'
                file_path.parent.mkdir(parents=True, exist_ok=True)

                reporter = HTMLReporter()
                reporter.generate(timeline, file_path, open_browser=open_browser, theme=theme)
                click.echo(click.style(f"  ✓ HTML: {file_path.name}", fg='green'))

                if open_browser:
                    click.echo(f"  🌐 Opening in browser...")

            elif fmt == 'executive':
                file_path = output_path if 'executive' in str(output_path) else output_path / 'executive_summary.html'
                file_path.parent.mkdir(parents=True, exist_ok=True)

                reporter = HTMLReporter()
                reporter.generate_executive_summary(timeline, file_path)
                click.echo(click.style(f"  ✓ Executive: {file_path.name}", fg='green'))

        # Summary
        click.echo("\n" + "=" * 50)
        click.echo(click.style("✓ Report generation complete!", fg='green', bold=True))

        if format == 'all':
            click.echo(f"\nReports saved to: {output_path}")
            for file in output_path.glob('*'):
                if file.is_file():
                    click.echo(f"  • {file.name}")
        else:
            final_path = output_path if output_path.suffix else list(output_path.glob('*'))[0]
            click.echo(f"\nReport saved: {final_path}")

            if fmt in ['html', 'executive'] and not open_browser:
                click.echo(f"\n🌐 Open: file://{final_path.absolute()}")

    except Exception as e:
        click.echo(click.style(f"\n❌ Report generation failed: {e}", fg='red'))
        if verbose:
            import traceback
            traceback.print_exc()
