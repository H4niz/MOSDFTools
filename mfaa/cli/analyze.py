"""
Analyze Command
===============

Full analysis pipeline: collect → parse → analyze → generate timeline → report.
"""

import click
import sys
import yaml
from pathlib import Path
from datetime import datetime
from mfaa.collector.volume_scanner import VolumeScanner
from mfaa.collector.fsevents_collector import FSEventsCollector
from mfaa.parser.fsevents_parser import FSEventsParser
from mfaa.analyzer.event_filter import EventFilter
from mfaa.analyzer.priority_scorer import PriorityScorer
from mfaa.analyzer.pattern_detector import PatternDetector
from mfaa.timeline.generator import TimelineGenerator
from mfaa.reporter import CSVReporter, JSONReporter, HTMLReporter
from mfaa.models import FilterConfig, ScoringWeights


@click.command()
@click.option(
    '--volume',
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    default='/',
    help='Volume to analyze (default: /)'
)
@click.option(
    '--output', '-o',
    type=click.Path(file_okay=False, resolve_path=True),
    required=True,
    help='Output directory for reports'
)
@click.option(
    '--format',
    type=click.Choice(['csv', 'json', 'html', 'all'], case_sensitive=False),
    default='html',
    help='Report format (default: html)'
)
@click.option(
    '--filter-config',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    help='YAML filter configuration file'
)
@click.option(
    '--min-priority',
    type=int,
    default=0,
    help='Minimum priority score (0-100, default: 0)'
)
@click.option(
    '--time-range',
    nargs=2,
    type=str,
    help='Time range filter: START END (YYYY-MM-DD format)'
)
@click.option(
    '--skip-collection',
    is_flag=True,
    help='Skip collection (use existing parsed data)'
)
@click.option(
    '--input',
    type=click.Path(exists=True, resolve_path=True),
    help='Input file (parsed JSON) when --skip-collection is used'
)
@click.pass_context
def analyze(ctx, volume, output, format, filter_config, min_priority, time_range, skip_collection, input):
    """
    Perform full forensic analysis pipeline.

    Complete workflow: collect artifacts → parse FSEvents → filter/score →
    detect patterns → generate timeline → create reports.

    \b
    Examples:
        # Full analysis with HTML report
        sudo mfaa analyze --output ./reports

        # Analysis with custom filters
        sudo mfaa analyze --output ./reports --filter-config filters.yaml

        # High-priority events only
        sudo mfaa analyze --output ./reports --min-priority 70

        # Analyze already-parsed data
        mfaa analyze --skip-collection --input events.json --output ./reports

        # All report formats
        sudo mfaa analyze --output ./reports --format all

    \b
    Note:
        - Requires root/sudo unless --skip-collection is used
        - Creates timestamped output directory
        - Generates CSV, JSON, and/or HTML reports
    """
    verbose = ctx.obj.get('verbose', False)

    click.echo(click.style("mFAA Forensic Analysis Pipeline", fg='cyan', bold=True))
    click.echo("=" * 60)

    output_path = Path(output)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    analysis_dir = output_path / f"analysis_{timestamp}"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    events = []
    xattr_records = {}

    # Pipeline execution
    try:
        if skip_collection and input:
            # Skip to parsing from file
            click.echo("\n📂 Loading parsed data...")
            import json

            input_path = Path(input)
            with open(input_path, 'r') as f:
                data = json.load(f)

            # Reconstruct events
            from mfaa.models import FSEvent, EventFlags, EventType

            for event_data in data.get('events', []):
                event = FSEvent(
                    event_id=event_data['event_id'],
                    timestamp=datetime.fromisoformat(event_data['timestamp']),
                    path=Path(event_data['path']),
                    flags=EventFlags(event_data['flags']),
                    node_id=event_data['node_id']
                )
                events.append(event)

            click.echo(click.style(f"✓ Loaded {len(events)} events", fg='green'))

        else:
            # Full collection and parsing
            # Step 1: Collect
            click.echo("\n📦 Step 1/5: Collecting Artifacts")
            click.echo("-" * 60)

            scanner = VolumeScanner()
            volumes = scanner.scan_volumes()

            target_volume = None
            volume_path = Path(volume)
            for vol in volumes:
                if vol.mount_point == volume_path:
                    target_volume = vol
                    break

            if not target_volume:
                click.echo(click.style(f"❌ Volume not found: {volume}", fg='red'))
                sys.exit(1)

            click.echo(f"Target: {target_volume.mount_point}")

            # Step 1a: Try to collect FSEvents
            collection_successful = False
            try:
                collector = FSEventsCollector(
                    output_dir=analysis_dir / "collected",
                    verify_hashes=True
                )
                with click.progressbar(length=1, label='Collecting', show_eta=False) as bar:
                    result = collector.collect(target_volume)
                    bar.update(1)

                click.echo(click.style(f"✓ Collected {result.files_copied} files", fg='green'))
                collection_successful = True

            except Exception as e:
                click.echo(click.style(f"⚠️  FSEvents collection failed: {e}", fg='yellow'))
                click.echo(click.style("⚠️  Continuing with alternative data sources...", fg='yellow'))
                if verbose:
                    import traceback
                    traceback.print_exc()

            # Step 2: Parse (only if collection succeeded)
            if collection_successful:
                click.echo("\n📊 Step 2/5: Parsing FSEvents")
                click.echo("-" * 60)

                try:
                    parser = FSEventsParser()
                    fsevents_dir = analysis_dir / "collected"

                    # Find all collected files recursively
                    files = list(fsevents_dir.rglob('*'))
                    fsevents_files = [f for f in files if f.is_file() and not f.name.startswith('.')]

                    if not fsevents_files:
                        click.echo(click.style("⚠️  No FSEvents files found to parse", fg='yellow'))
                    else:
                        with click.progressbar(
                            fsevents_files,
                            label='Parsing files',
                            show_eta=True
                        ) as bar:
                            for file_path in bar:
                                try:
                                    file_events = parser.parse_file(file_path)
                                    events.extend(file_events)
                                except Exception as parse_error:
                                    if verbose:
                                        logger.warning(f"Failed to parse {file_path.name}: {parse_error}")

                        click.echo(click.style(f"✓ Parsed {len(events)} events", fg='green'))

                except Exception as e:
                    click.echo(click.style(f"⚠️  Parsing failed: {e}", fg='yellow'))
                    if verbose:
                        import traceback
                        traceback.print_exc()
            else:
                click.echo("\n📊 Step 2/5: Parsing FSEvents")
                click.echo("-" * 60)
                click.echo(click.style("⚠️  Skipped (collection failed)", fg='yellow'))

        # If no events from FSEvents, try to provide helpful information
        if not events:
            click.echo(click.style("\n❌ No FSEvents data available for analysis", fg='red'))
            click.echo("\n" + "=" * 60)
            click.echo(click.style("📋 Alternative Investigation Options:", fg='cyan', bold=True))
            click.echo("=" * 60)

            click.echo("\n1. Use the gather command to see available artifacts:")
            click.echo("   mfaa gather --volume / --output artifacts_scan.json")

            click.echo("\n2. Try the Data volume directly:")
            click.echo("   sudo mfaa analyze --volume /System/Volumes/Data --output ./analysis")

            click.echo("\n3. Collect other forensic artifacts manually:")
            click.echo("   • Chrome/Safari History: Browser browsing data")
            click.echo("   • System Logs: /var/log/")
            click.echo("   • Quarantine DB: Download/quarantine information")
            click.echo("   • Launch Agents/Daemons: Persistence mechanisms")

            click.echo("\n4. Check if FSEvents are available:")
            click.echo("   ls -la /.fseventsd")
            click.echo("   ls -la /System/Volumes/Data/.fseventsd")

            click.echo("\n" + "=" * 60)
            click.echo(click.style("💡 Tip:", fg='yellow', bold=True) + " On macOS Catalina+, FSEvents may be on")
            click.echo("   the Data volume. Try running gather first to identify")
            click.echo("   available forensic artifacts.")
            click.echo("=" * 60)

            sys.exit(1)

        # Step 3: Filter and Score
        click.echo("\n🔍 Step 3/5: Filtering & Scoring")
        click.echo("-" * 60)

        # Load filter config if provided
        filter_cfg = None
        if filter_config:
            click.echo(f"Loading filter config: {Path(filter_config).name}")
            with open(filter_config, 'r') as f:
                config_data = yaml.safe_load(f)
                filter_cfg = FilterConfig(**config_data)

        # Apply filters
        event_filter = EventFilter(filter_cfg)
        filtered_events = event_filter.filter_events(events)

        click.echo(f"After filtering: {len(filtered_events)} events")

        # Apply priority filter if specified
        if min_priority > 0:
            scorer = PriorityScorer()
            filtered_events = [
                e for e in filtered_events
                if scorer.calculate_score(e) >= min_priority
            ]
            click.echo(f"After priority filter (>={min_priority}): {len(filtered_events)} events")

        click.echo(click.style(f"✓ {len(filtered_events)} events ready for analysis", fg='green'))

        # Step 4: Generate Timeline
        click.echo("\n📅 Step 4/5: Generating Timeline")
        click.echo("-" * 60)

        generator = TimelineGenerator()

        with click.progressbar(length=1, label='Analyzing', show_eta=False) as bar:
            timeline = generator.generate_timeline(
                filtered_events,
                xattr_records=xattr_records,
                detect_patterns=True
            )
            bar.update(1)

        click.echo(click.style(f"✓ Timeline generated", fg='green'))
        click.echo(f"  Events: {len(timeline.entries)}")
        click.echo(f"  Patterns: {len(timeline.patterns)}")

        if timeline.patterns:
            critical = sum(1 for p in timeline.patterns if p.severity == 'CRITICAL')
            high = sum(1 for p in timeline.patterns if p.severity == 'HIGH')
            if critical > 0:
                click.echo(click.style(f"  ⚠️  {critical} CRITICAL patterns detected!", fg='red', bold=True))
            if high > 0:
                click.echo(click.style(f"  ⚠️  {high} HIGH severity patterns", fg='yellow'))

        # Step 5: Generate Reports
        click.echo("\n📄 Step 5/5: Generating Reports")
        click.echo("-" * 60)

        formats_to_generate = []
        if format == 'all':
            formats_to_generate = ['csv', 'json', 'html']
        else:
            formats_to_generate = [format]

        for fmt in formats_to_generate:
            click.echo(f"Generating {fmt.upper()} report...")

            if fmt == 'csv':
                reporter = CSVReporter()
                reporter.generate(
                    timeline,
                    analysis_dir / "report.csv",
                    include_patterns=True,
                    include_statistics=True
                )
                click.echo(click.style(f"  ✓ CSV: report.csv", fg='green'))

            elif fmt == 'json':
                reporter = JSONReporter()
                reporter.generate(
                    timeline,
                    analysis_dir / "report.json",
                    pretty=True
                )
                click.echo(click.style(f"  ✓ JSON: report.json", fg='green'))

            elif fmt == 'html':
                reporter = HTMLReporter()
                reporter.generate(
                    timeline,
                    analysis_dir / "report.html",
                    open_browser=False
                )
                click.echo(click.style(f"  ✓ HTML: report.html", fg='green'))

                # Also generate executive summary
                reporter.generate_executive_summary(
                    timeline,
                    analysis_dir / "executive_summary.html"
                )
                click.echo(click.style(f"  ✓ Executive: executive_summary.html", fg='green'))

        # Final Summary
        click.echo("\n" + "=" * 60)
        click.echo(click.style("✓ Analysis Complete!", fg='green', bold=True))
        click.echo(f"\nResults saved to: {analysis_dir}")

        if verbose:
            click.echo("\nSummary:")
            click.echo(f"  Total events analyzed: {len(events)}")
            click.echo(f"  Events after filtering: {len(filtered_events)}")
            click.echo(f"  Timeline entries: {len(timeline.entries)}")
            click.echo(f"  Patterns detected: {len(timeline.patterns)}")

        click.echo("\nGenerated files:")
        for file in analysis_dir.glob('*'):
            if file.is_file():
                size = file.stat().st_size / 1024
                click.echo(f"  • {file.name} ({size:.1f} KB)")

        if 'html' in formats_to_generate:
            html_path = analysis_dir / "report.html"
            click.echo(f"\n🌐 Open report: file://{html_path.absolute()}")

    except KeyboardInterrupt:
        click.echo("\n\n❌ Analysis cancelled by user")
        sys.exit(130)

    except Exception as e:
        click.echo(click.style(f"\n❌ Analysis failed: {e}", fg='red'))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
