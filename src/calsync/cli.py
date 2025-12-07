"""CLI interface for CalSync."""

import logging
from datetime import datetime, timedelta

import click

from calsync.adapters.eventkit import EventKitAdapter
from calsync.config import Config


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def cli(verbose: bool) -> None:
    """CalSync - Bidirectional calendar sync for macOS."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


@cli.command("list-calendars")
def list_calendars() -> None:
    """List all available calendars."""
    adapter = EventKitAdapter()
    calendars = adapter.get_calendars()

    click.echo("\nAvailable calendars:\n")
    for cal in calendars:
        writable = "rw" if cal["writable"] else "ro"
        click.echo(f"  [{writable}] {cal['name']}")
        click.echo(f"       ID: {cal['id']}")
        click.echo(f"       Source: {cal['source']}")
        click.echo()


@cli.command()
def configure() -> None:
    """Configure the calendars to sync."""
    adapter = EventKitAdapter()
    calendars = adapter.get_calendars()

    # Only show writable calendars
    writable = [c for c in calendars if c["writable"]]

    if len(writable) < 2:
        click.echo("Error: Need at least 2 writable calendars.")
        return

    click.echo("\nWritable calendars:\n")
    for i, cal in enumerate(writable, 1):
        click.echo(f"  {i}. {cal['name']} ({cal['source']})")

    click.echo()
    a_idx = click.prompt("Calendar A (number)", type=int) - 1
    b_idx = click.prompt("Calendar B (number)", type=int) - 1

    if a_idx == b_idx:
        click.echo("Error: Please select two different calendars.")
        return

    if not (0 <= a_idx < len(writable) and 0 <= b_idx < len(writable)):
        click.echo("Error: Invalid selection.")
        return

    config = Config(
        calendar_a_id=writable[a_idx]["id"],
        calendar_a_name=writable[a_idx]["name"],
        calendar_b_id=writable[b_idx]["id"],
        calendar_b_name=writable[b_idx]["name"],
    )
    config.save()

    click.echo(f"\nConfiguration saved:")
    click.echo(f"  A: {config.calendar_a_name}")
    click.echo(f"  B: {config.calendar_b_name}")


@cli.command()
@click.option("--days", "-d", default=30, help="Number of days to sync")
@click.option("--dry-run", is_flag=True, help="Only simulate, don't make changes")
def sync(days: int, dry_run: bool) -> None:
    """Sync placeholders between configured calendars."""
    config = Config.load()

    if not config.is_configured():
        click.echo("Error: Calendars not configured. Run 'calsync configure' first.")
        return

    # Import here to avoid circular imports
    from calsync.sync.engine import SyncEngine

    adapter = EventKitAdapter()
    engine = SyncEngine(
        adapter=adapter,
        calendar_a_id=config.calendar_a_id,
        calendar_b_id=config.calendar_b_id,
    )

    end_date = datetime.now() + timedelta(days=days)

    if dry_run:
        click.echo("=== DRY RUN - No changes will be made ===\n")

    result_a_b, result_b_a = engine.sync(end_date=end_date, dry_run=dry_run)

    click.echo(f"\nSync {config.calendar_a_name} -> {config.calendar_b_name}:")
    click.echo(
        f"  {result_a_b.created} created, "
        f"{result_a_b.updated} updated, "
        f"{result_a_b.deleted} deleted"
    )

    click.echo(f"\nSync {config.calendar_b_name} -> {config.calendar_a_name}:")
    click.echo(
        f"  {result_b_a.created} created, "
        f"{result_b_a.updated} updated, "
        f"{result_b_a.deleted} deleted"
    )

    all_errors = result_a_b.errors + result_b_a.errors
    if all_errors:
        click.echo("\nErrors:")
        for err in all_errors:
            click.echo(f"  - {err}")


@cli.command()
def status() -> None:
    """Show current configuration and sync status."""
    config = Config.load()

    if not config.is_configured():
        click.echo("Not configured. Run 'calsync configure' first.")
        return

    click.echo(f"\nConfigured calendars:")
    click.echo(f"  A: {config.calendar_a_name}")
    click.echo(f"  B: {config.calendar_b_name}")


if __name__ == "__main__":
    cli()
