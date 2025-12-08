"""CLI interface for CalSync."""

import logging
from datetime import datetime, timedelta
from typing import Optional

import click

from calsync.adapters.eventkit import EventKitAdapter
from calsync.config import CalendarConfig, Config


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--profile", "-p", default=None, help="Configuration profile name")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, profile: Optional[str]) -> None:
    """CalSync - Multi-calendar sync for macOS."""
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile

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
@click.pass_context
def configure(ctx: click.Context) -> None:
    """Configure the calendars to sync."""
    profile = ctx.obj.get("profile")
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

    click.echo("\nEnter calendar numbers to sync (comma-separated, e.g. '1,2,3'):")
    selection = click.prompt("Calendars", type=str)

    try:
        indices = [int(x.strip()) - 1 for x in selection.split(",")]
    except ValueError:
        click.echo("Error: Invalid input. Use comma-separated numbers.")
        return

    if len(indices) < 2:
        click.echo("Error: Select at least 2 calendars.")
        return

    if len(indices) != len(set(indices)):
        click.echo("Error: Duplicate selections not allowed.")
        return

    if not all(0 <= i < len(writable) for i in indices):
        click.echo("Error: Invalid calendar number.")
        return

    selected = [
        CalendarConfig(id=writable[i]["id"], name=writable[i]["name"])
        for i in indices
    ]

    config = Config(calendars=selected, profile=profile)
    config.save()

    profile_info = f" (profile: {profile})" if profile else ""
    click.echo(f"\nConfiguration saved{profile_info} ({len(selected)} calendars):")
    for i, cal in enumerate(selected, 1):
        click.echo(f"  {i}. {cal.name}")


@cli.command()
@click.option("--days", "-d", default=30, help="Number of days to sync")
@click.option("--dry-run", is_flag=True, help="Only simulate, don't make changes")
@click.pass_context
def sync(ctx: click.Context, days: int, dry_run: bool) -> None:
    """Sync placeholders between configured calendars."""
    profile = ctx.obj.get("profile")
    config = Config.load(profile)

    if not config.is_configured():
        profile_hint = f" for profile '{profile}'" if profile else ""
        click.echo(f"Error: Calendars not configured{profile_hint}. Run 'calsync configure' first.")
        return

    from calsync.sync.engine import SyncEngine

    adapter = EventKitAdapter()
    engine = SyncEngine(
        adapter=adapter,
        calendar_ids=config.get_calendar_ids(),
    )

    # Ende: Mitternacht in `days` Tagen (lokale Zeitzone)
    # -d 1 = heute bis Tagesende, -d 2 = bis morgen Tagesende, etc.
    today_midnight = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today_midnight + timedelta(days=days)

    if dry_run:
        click.echo("=== DRY RUN - No changes will be made ===\n")

    summary = engine.sync(end_date=end_date, dry_run=dry_run)

    # Group results by target calendar
    profile_info = f" [profile: {profile}]" if profile else ""
    click.echo(f"\nSync summary ({len(config.calendars)} calendars){profile_info}:\n")

    for result in summary.results:
        if result.total_actions > 0:
            source_name = config.get_calendar_name(result.source_id)
            target_name = config.get_calendar_name(result.target_id)
            click.echo(
                f"  {source_name} -> {target_name}: "
                f"{result.created} created, "
                f"{result.updated} updated, "
                f"{result.deleted} deleted"
            )

    total = summary.total_created + summary.total_updated + summary.total_deleted
    if total == 0:
        click.echo("  No changes needed.")
    else:
        click.echo(
            f"\nTotal: {summary.total_created} created, "
            f"{summary.total_updated} updated, "
            f"{summary.total_deleted} deleted"
        )

    if summary.all_errors:
        click.echo("\nErrors:")
        for err in summary.all_errors:
            click.echo(f"  - {err}")


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show current configuration."""
    profile = ctx.obj.get("profile")
    config = Config.load(profile)

    if not config.is_configured():
        profile_hint = f" for profile '{profile}'" if profile else ""
        click.echo(f"Not configured{profile_hint}. Run 'calsync configure' first.")
        return

    profile_info = f" [profile: {profile}]" if profile else ""
    click.echo(f"\nConfigured calendars ({len(config.calendars)}){profile_info}:\n")
    for i, cal in enumerate(config.calendars, 1):
        click.echo(f"  {i}. {cal.name}")


if __name__ == "__main__":
    cli()
