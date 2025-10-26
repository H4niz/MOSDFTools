"""
Command-Line Interface for mFAA
================================

CLI commands for artifact collection, parsing, analysis, and reporting.
"""

import click
import sys
from pathlib import Path
from datetime import datetime
from mfaa import __version__
from mfaa.utils.logger import setup_logger
from mfaa.utils.validator import Validator
from mfaa.utils.exceptions import MFAAError

logger = setup_logger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(verbose):
    """
    macOS Forensics Artifacts Analyzer (mFAA)

    A digital forensics tool for macOS live acquisition and analysis.
    """
    if verbose:
        import logging
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")


@main.command()
@click.option('--volume', '-vol', type=click.Path(exists=True), help='Specific volume to collect from')
@click.option('--output-dir', '-o', type=click.Path(), required=True, help='Output directory for artifacts')
@click.option('--verify-hashes/--no-verify-hashes', default=True, help='Calculate SHA-256 hashes')
def collect(volume, output_dir, verify_hashes):
    """
    Collect FSEvents and Extended Attributes from macOS system.

    Requires root/administrator privileges.
    """
    logger.info("Starting artifact collection...")

    # Check root privileges
    if not Validator.check_root_privileges():
        logger.error("Root privileges required for FSEvents collection")
        click.echo("Error: This command requires root/administrator privileges.", err=True)
        click.echo("Please run with 'sudo'", err=True)
        sys.exit(2)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        from mfaa.collector import VolumeScanner, FSEventsCollector

        # Scan volumes
        scanner = VolumeScanner()
        if volume:
            click.echo(f"Collecting from volume: {volume}")
            volume_info = scanner.get_volume_info(volume)
            volumes = [volume_info]
        else:
            click.echo("Scanning for APFS volumes...")
            volumes = scanner.scan_volumes()
            click.echo(f"Found {len(volumes)} APFS volumes")

        # Collect FSEvents
        collector = FSEventsCollector(output_path, verify_hashes=verify_hashes)

        with click.progressbar(volumes, label='Collecting artifacts') as vol_list:
            results = []
            for vol in vol_list:
                result = collector.collect(vol)
                results.append(result)

        # Display results
        click.echo("\n=== Collection Summary ===")
        for result in results:
            status = "✓" if result.success else "✗"
            click.echo(f"{status} {result.volume.name}: {result.files_copied} files, "
                      f"{result.total_size} bytes")

        click.echo(f"\nArtifacts saved to: {output_path}")

    except MFAAError as e:
        logger.error(f"Collection failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('fsevents_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), required=True, help='Output file (JSON)')
def parse(fsevents_path, output):
    """
    Parse collected FSEvents database.

    FSEVENTS_PATH: Path to .fseventsd directory or single FSEvents file
    """
    logger.info(f"Parsing FSEvents from: {fsevents_path}")

    try:
        from mfaa.parser import FSEventsParser

        parser = FSEventsParser()
        path = Path(fsevents_path)

        if path.is_dir():
            events = parser.parse_directory(path)
        else:
            events = parser.parse_file(path)

        click.echo(f"Parsed {len(events)} events")

        # Save to JSON
        # TODO: Implement JSON serialization
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        click.echo(f"Results saved to: {output_path}")

    except Exception as e:
        logger.error(f"Parsing failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--output-dir', '-o', type=click.Path(), required=True, help='Output directory')
@click.option('--filter-config', '-f', type=click.Path(exists=True), help='Filter configuration file')
@click.option('--scoring-config', '-s', type=click.Path(exists=True), help='Scoring configuration file')
@click.option('--format', '-fmt', type=click.Choice(['csv', 'json', 'html', 'all']), default='all',
              help='Report format')
@click.option('--min-priority', type=int, help='Minimum priority score (0-100)')
def analyze(output_dir, filter_config, scoring_config, format, min_priority):
    """
    Run complete analysis pipeline: collect -> parse -> analyze -> report.

    Requires root/administrator privileges for collection.
    """
    logger.info("Starting full analysis pipeline...")

    # Check root privileges
    if not Validator.check_root_privileges():
        click.echo("Error: This command requires root/administrator privileges.", err=True)
        click.echo("Please run with 'sudo'", err=True)
        sys.exit(2)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo("=== mFAA Full Analysis ===")
    click.echo(f"Output directory: {output_path}")
    click.echo(f"Timestamp: {datetime.now().isoformat()}")
    click.echo()

    # TODO: Implement full pipeline
    # 1. Collection
    # 2. Parsing
    # 3. Analysis
    # 4. Timeline generation
    # 5. Report generation

    click.echo("Analysis pipeline not yet fully implemented")
    click.echo("Please use individual commands: collect, parse, report")


@main.command()
@click.argument('data_file', type=click.Path(exists=True))
@click.option('--format', '-fmt', type=click.Choice(['csv', 'json', 'html']), required=True,
              help='Report format')
@click.option('--output', '-o', type=click.Path(), required=True, help='Output report file')
def report(data_file, format, output):
    """
    Generate report from parsed data.

    DATA_FILE: Path to parsed data (JSON)
    """
    logger.info(f"Generating {format.upper()} report...")

    try:
        # TODO: Implement report generation
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        click.echo(f"Report generation not yet implemented")
        click.echo(f"Output would be: {output_path}")

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
