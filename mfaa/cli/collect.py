"""
Collect Command
===============

Collect forensic artifacts from macOS volumes.
"""

import click
import os
import sys
from pathlib import Path
from datetime import datetime
from mfaa.collector.volume_scanner import VolumeScanner
from mfaa.collector.fsevents_collector import FSEventsCollector
from mfaa.collector.xattr_collector import XattrCollector


@click.command()
@click.option(
    '--volume',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default='/',
    help='Volume to collect from (default: /)'
)
@click.option(
    '--output', '-o',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
    help='Output directory for collected artifacts'
)
@click.option(
    '--include-xattr/--no-xattr',
    default=True,
    help='Collect extended attributes (default: yes)'
)
@click.option(
    '--verify-hashes/--no-verify',
    default=True,
    help='Calculate SHA-256 hashes (default: yes)'
)
@click.pass_context
def collect(ctx, volume, output, include_xattr, verify_hashes):
    """
    Collect forensic artifacts from macOS volume.

    Collects FSEvents database files and optionally extended attributes
    with hash verification for chain of custody.

    \b
    Examples:
        # Collect from root volume
        sudo mfaa collect --output ./artifacts

        # Collect from external volume
        sudo mfaa collect --volume /Volumes/External --output ./case001

        # Collect without xattr
        sudo mfaa collect --output ./artifacts --no-xattr

    \b
    Note:
        - Requires root/sudo for accessing .fseventsd
        - Creates timestamped collection directory
        - Generates acquisition log with metadata
    """
    verbose = ctx.obj.get('verbose', False)

    click.echo(click.style("mFAA Artifact Collector", fg='cyan', bold=True))
    click.echo("=" * 50)

    # Check root privileges
    if os.geteuid() != 0:
        click.echo(click.style(
            "⚠️  Warning: Not running as root. FSEvents collection may fail.",
            fg='yellow'
        ))
        if not click.confirm("Continue anyway?"):
            sys.exit(1)

    # Create output directory
    output_path = Path(output)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    collection_dir = output_path / f"collection_{timestamp}"
    collection_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        click.echo(f"Output directory: {collection_dir}")

    # Step 1: Scan volumes
    click.echo("\n📊 Scanning volumes...")
    scanner = VolumeScanner()
    volumes = scanner.scan_volumes()

    if not volumes:
        click.echo(click.style("❌ No volumes found!", fg='red'))
        sys.exit(1)

    # Find target volume
    target_volume = None
    volume_path = Path(volume)

    for vol in volumes:
        if vol.mount_point == volume_path:
            target_volume = vol
            break

    if not target_volume:
        click.echo(click.style(f"❌ Volume not found: {volume}", fg='red'))
        click.echo("\nAvailable volumes:")
        for vol in volumes:
            click.echo(f"  • {vol.mount_point} ({vol.filesystem})")
        sys.exit(1)

    click.echo(click.style(f"✓ Target volume: {target_volume.mount_point}", fg='green'))
    if verbose:
        click.echo(f"  Filesystem: {target_volume.filesystem}")
        click.echo(f"  Device: {target_volume.device_identifier}")

    # Step 2: Collect FSEvents
    click.echo("\n📦 Collecting FSEvents...")
    fsevents_output = collection_dir / "fsevents"
    fsevents_collector = FSEventsCollector(
        output_dir=fsevents_output,
        verify_hashes=verify_hashes
    )

    with click.progressbar(
        length=1,
        label='Collecting FSEvents',
        show_eta=False
    ) as bar:
        try:
            result = fsevents_collector.collect(
                target_volume,
                create_log=True
            )
            bar.update(1)

            click.echo(click.style(f"✓ Collected {len(result.collected_files)} files", fg='green'))

            if verify_hashes and result.checksums:
                click.echo(f"  SHA-256 hashes calculated: {len(result.checksums)}")

            # Save acquisition log
            if result.acquisition_log_path:
                click.echo(f"  Acquisition log: {result.acquisition_log_path.name}")

        except Exception as e:
            click.echo(click.style(f"❌ FSEvents collection failed: {e}", fg='red'))
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    # Step 3: Collect Extended Attributes (optional)
    if include_xattr:
        click.echo("\n🏷️  Collecting Extended Attributes...")
        xattr_collector = XattrCollector()

        # Get paths from FSEvents for xattr collection
        # For now, just collect from common suspicious locations
        suspicious_paths = [
            target_volume.mount_point / "Users",
            target_volume.mount_point / "Applications",
            target_volume.mount_point / "Library"
        ]

        xattr_output = collection_dir / "xattr_records.json"

        with click.progressbar(
            length=len(suspicious_paths),
            label='Scanning directories',
            show_eta=False
        ) as bar:
            all_records = []
            for path in suspicious_paths:
                if path.exists():
                    try:
                        records = xattr_collector.collect_from_directory(
                            path,
                            recursive=False  # Top-level only for speed
                        )
                        all_records.extend(records)
                    except Exception as e:
                        if verbose:
                            click.echo(f"  Warning: Could not scan {path}: {e}")
                bar.update(1)

            # Save to JSON
            if all_records:
                xattr_collector.save_to_json(all_records, xattr_output)
                click.echo(click.style(f"✓ Collected {len(all_records)} xattr records", fg='green'))
            else:
                click.echo("  No xattr records found")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo(click.style("✓ Collection Complete!", fg='green', bold=True))
    click.echo(f"\nArtifacts saved to: {collection_dir}")
    click.echo("\nNext steps:")
    click.echo(f"  1. Parse: mfaa parse {collection_dir}/fsevents --output timeline.json")
    click.echo(f"  2. Analyze: mfaa analyze {collection_dir} --output reports/")
