"""
Main CLI Entry Point
====================

mFAA command-line interface.
"""

import click
import sys
from pathlib import Path

# Import commands
from mfaa.cli.collect import collect
from mfaa.cli.parse_cmd import parse
from mfaa.cli.analyze import analyze
from mfaa.cli.report_cmd import report as report_cmd


@click.group()
@click.version_option(version='1.0.0', prog_name='mFAA')
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, verbose, debug):
    """
    mFAA - macOS Forensics Artifacts Analyzer

    A comprehensive tool for analyzing macOS file system events and artifacts.

    \b
    Usage Examples:
        # Full analysis of current system
        sudo mfaa analyze --output ./reports

        # Collect artifacts only
        sudo mfaa collect --volume /Volumes/MacHD --output ./artifacts

        # Parse collected FSEvents
        mfaa parse ./artifacts/fsevents --output ./parsed.json

        # Generate HTML report
        mfaa report ./timeline.json --format html --output report.html

    \b
    For more information on a specific command:
        mfaa COMMAND --help
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj['verbose'] = verbose
    ctx.obj['debug'] = debug

    # Setup logging based on verbosity
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        import logging
        logging.basicConfig(level=logging.INFO)


# Register commands
cli.add_command(collect)
cli.add_command(parse)
cli.add_command(analyze)
cli.add_command(report_cmd)


def main():
    """Entry point for CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user.", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
