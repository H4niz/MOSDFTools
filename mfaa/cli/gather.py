"""
Gather Command
==============

Scan and list available forensic artifacts on macOS volumes.
"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from mfaa.collector.volume_scanner import VolumeScanner
from mfaa.collector.artifact_scanner import ArtifactScanner


@click.command()
@click.option(
    '--volume',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default='/',
    help='Volume to scan (default: /)'
)
@click.option(
    '--output', '-o',
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    help='Save results to JSON file'
)
@click.option(
    '--category',
    type=click.Choice(['all', 'filesystem', 'system', 'application', 'user']),
    default='all',
    help='Filter by artifact category'
)
@click.option(
    '--show-commands/--no-commands',
    default=True,
    help='Show collection commands (default: yes)'
)
@click.pass_context
def gather(ctx, volume, output, category, show_commands):
    """
    Scan and list available forensic artifacts on macOS volume.

    This command performs a comprehensive scan of the specified volume
    to identify which forensic artifacts exist and are accessible.
    It provides collection commands for each artifact found.

    \b
    Examples:
        # Scan root volume
        mfaa gather

        # Scan specific volume
        mfaa gather --volume /Volumes/MacHD

        # Show only filesystem artifacts
        mfaa gather --category filesystem

        # Save results to file
        mfaa gather --output artifacts_scan.json

    \b
    Artifact Categories:
        - filesystem: FSEvents, Spotlight
        - system: Unified Logs, LaunchDaemons, TCC
        - application: Browser history, Application lists
        - user: Shell history, Recent items, Downloads

    \b
    Note:
        - Some artifacts require root/sudo access
        - Results show which artifacts are currently accessible
        - Use collection commands to gather artifacts
    """
    verbose = ctx.obj.get('verbose', False)

    click.echo(click.style("mFAA Artifact Gatherer", fg='cyan', bold=True))
    click.echo("=" * 70)

    # Step 1: Scan volume
    click.echo(f"\n📊 Scanning volume: {volume}")
    scanner = VolumeScanner()

    try:
        volumes = scanner.scan_volumes()
        target_volume = None
        volume_path = Path(volume)

        for vol in volumes:
            if vol.mount_point == volume_path:
                target_volume = vol
                break

        if not target_volume:
            # Try to get info directly if not in APFS list
            try:
                target_volume = scanner.get_volume_info(volume)
            except Exception as e:
                click.echo(click.style(f"❌ Volume not found: {volume}", fg='red'))
                click.echo(f"Error: {e}")
                sys.exit(1)

        click.echo(click.style(f"✓ Volume: {target_volume.name}", fg='green'))
        if verbose:
            click.echo(f"  Mount point: {target_volume.mount_point}")
            click.echo(f"  Filesystem: {target_volume.filesystem_type}")
            click.echo(f"  Encrypted: {target_volume.encryption_enabled}")

    except Exception as e:
        click.echo(click.style(f"❌ Failed to scan volume: {e}", fg='red'))
        sys.exit(1)

    # Step 2: Scan for artifacts
    click.echo("\n🔍 Scanning for forensic artifacts...")
    artifact_scanner = ArtifactScanner()

    try:
        scan_result = artifact_scanner.scan_volume(target_volume)

        click.echo(click.style(
            f"✓ Found {scan_result.total_found} artifacts "
            f"({scan_result.accessible_count} accessible)",
            fg='green'
        ))

    except Exception as e:
        click.echo(click.style(f"❌ Artifact scan failed: {e}", fg='red'))
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Step 3: Display results by category
    click.echo("\n" + "=" * 70)
    click.echo(click.style("Artifact Summary", fg='cyan', bold=True))
    click.echo("=" * 70)

    categories_to_show = ['filesystem', 'system', 'application', 'user'] \
        if category == 'all' else [category]

    total_shown = 0

    for cat in categories_to_show:
        artifacts = scan_result.get_by_category(cat)
        accessible = [a for a in artifacts if a.exists and a.readable]

        if not artifacts:
            continue

        click.echo(f"\n{_get_category_icon(cat)} {cat.upper()}")
        click.echo("-" * 70)

        for artifact in artifacts:
            total_shown += 1

            # Status indicator
            if artifact.exists and artifact.readable:
                status = click.style("✓", fg='green')
            elif artifact.exists and not artifact.readable:
                status = click.style("⚠", fg='yellow')
            else:
                status = click.style("✗", fg='red')

            # Root indicator
            root_indicator = click.style(" [ROOT]", fg='red', bold=True) \
                if artifact.requires_root else ""

            click.echo(f"\n{status} {artifact.name}{root_indicator}")

            if verbose or not artifact.exists:
                click.echo(f"   Path: {artifact.path}")

            if artifact.exists:
                if artifact.size is not None:
                    size_mb = artifact.size / (1024 * 1024)
                    click.echo(f"   Size: {size_mb:.2f} MB")
                if artifact.item_count is not None:
                    click.echo(f"   Items: {artifact.item_count}")

                if not artifact.readable:
                    click.echo(
                        click.style(
                            "   ⚠ Not readable (requires elevated privileges)",
                            fg='yellow'
                        )
                    )

            if verbose and artifact.description:
                click.echo(f"   Description: {artifact.description}")

            if show_commands and artifact.exists and artifact.readable:
                click.echo(click.style(
                    f"   Command: {artifact.collection_command}",
                    fg='blue'
                ))

    # Step 4: Generate collection guide
    click.echo("\n" + "=" * 70)
    click.echo(click.style("Collection Guide", fg='cyan', bold=True))
    click.echo("=" * 70)

    guide = artifact_scanner.generate_collection_guide(scan_result)

    click.echo(f"\nTotal artifacts found: {scan_result.total_found}")
    click.echo(f"Accessible now: {scan_result.accessible_count}")
    click.echo(f"Require root: {guide['summary']['requires_root']}")

    # Show collection steps
    if guide['collection_steps']:
        click.echo("\n" + click.style("Recommended Collection Steps:", fg='yellow'))

        for step in guide['collection_steps']:
            click.echo(f"\n{step['step']}. {step['title']}")
            click.echo(f"   {step['note']}")

            if verbose:
                click.echo("\n   Artifacts in this step:")
                for cmd_info in step['commands'][:3]:  # Show first 3
                    click.echo(f"   - {cmd_info['artifact']}")

                if len(step['commands']) > 3:
                    remaining = len(step['commands']) - 3
                    click.echo(f"   ... and {remaining} more")

        # Quick start command
        click.echo("\n" + click.style("Quick Start:", fg='green', bold=True))
        click.echo(f"  sudo mfaa collect --volume {target_volume.mount_point} --output ./artifacts")

    # Step 5: Save to file if requested
    if output:
        try:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(guide, f, indent=2, ensure_ascii=False)

            click.echo(f"\n💾 Results saved to: {output_path}")

        except Exception as e:
            click.echo(click.style(f"\n❌ Failed to save results: {e}", fg='red'))

    click.echo("\n" + "=" * 70)
    click.echo(click.style("✓ Scan Complete!", fg='green', bold=True))
    click.echo("\nNext steps:")
    click.echo(f"  1. Review accessible artifacts above")
    click.echo(f"  2. Run: sudo mfaa collect --volume {volume} --output ./case001")
    click.echo(f"  3. Analyze: mfaa analyze ./case001 --output ./reports")


def _get_category_icon(category: str) -> str:
    """Get emoji icon for category."""
    icons = {
        'filesystem': '💾',
        'system': '⚙️',
        'application': '📱',
        'user': '👤'
    }
    return icons.get(category, '📦')
