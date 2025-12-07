"""Main sync engine."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import permutations

from calsync.adapters.base import CalendarAdapter
from calsync.models.event import CalendarEvent
from calsync.models.placeholder import PlaceholderInfo
from calsync.sync.differ import ChangeDiffer, ChangeType
from calsync.sync.tracker import EventTracker

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a sync operation."""

    source_id: str = ""
    target_id: str = ""
    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total_actions(self) -> int:
        return self.created + self.updated + self.deleted


@dataclass
class SyncSummary:
    """Summary of all sync operations."""

    results: list[SyncResult] = field(default_factory=list)

    @property
    def total_created(self) -> int:
        return sum(r.created for r in self.results)

    @property
    def total_updated(self) -> int:
        return sum(r.updated for r in self.results)

    @property
    def total_deleted(self) -> int:
        return sum(r.deleted for r in self.results)

    @property
    def all_errors(self) -> list[str]:
        return [e for r in self.results for e in r.errors]


class SyncEngine:
    """Main sync logic for multi-calendar sync."""

    PLACEHOLDER_TITLE = "Nicht verfügbar"

    def __init__(
        self,
        adapter: CalendarAdapter,
        calendar_ids: list[str],
    ):
        self.adapter = adapter
        self.calendar_ids = calendar_ids
        self.tracker = EventTracker()
        self.differ = ChangeDiffer(self.tracker)

    def sync(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        dry_run: bool = False,
    ) -> SyncSummary:
        """
        Perform sync between all calendar pairs.

        For n calendars, syncs each calendar to all others.

        Args:
            start_date: Start of sync period (default: today)
            end_date: End of sync period (default: +30 days)
            dry_run: If True, only simulate changes

        Returns:
            SyncSummary with results for each direction
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if end_date is None:
            end_date = start_date + timedelta(days=30)

        logger.info(f"Sync period: {start_date.date()} to {end_date.date()}")
        logger.info(f"Calendars: {len(self.calendar_ids)}")

        summary = SyncSummary()

        # Load events from all calendars
        events_by_calendar: dict[str, list[CalendarEvent]] = {}
        for cal_id in self.calendar_ids:
            events = self.adapter.get_events(cal_id, start_date, end_date)
            events_by_calendar[cal_id] = events
            logger.info(f"Calendar {cal_id[:8]}...: {len(events)} events")

        # Sync each pair (source -> target)
        for source_id, target_id in permutations(self.calendar_ids, 2):
            result = self._sync_direction(
                source_events=events_by_calendar[source_id],
                target_events=events_by_calendar[target_id],
                source_cal_id=source_id,
                target_cal_id=target_id,
                dry_run=dry_run,
            )
            result.source_id = source_id
            result.target_id = target_id
            summary.results.append(result)

            # Refresh target events if changes were made
            if not dry_run and result.total_actions > 0:
                events_by_calendar[target_id] = self.adapter.get_events(
                    target_id, start_date, end_date
                )

        return summary

    def _sync_direction(
        self,
        source_events: list[CalendarEvent],
        target_events: list[CalendarEvent],
        source_cal_id: str,
        target_cal_id: str,
        dry_run: bool,
    ) -> SyncResult:
        """Sync in one direction."""
        result = SyncResult()

        actions = self.differ.compute_sync_actions(
            source_events, target_events, source_cal_id
        )

        logger.debug(
            f"Direction {source_cal_id[:8]}... -> {target_cal_id[:8]}...: {len(actions)} actions"
        )

        for action in actions:
            try:
                if action.action_type == ChangeType.CREATE:
                    if not dry_run:
                        self._create_placeholder(
                            action.source_event,
                            source_cal_id,
                            target_cal_id,
                        )
                    result.created += 1
                    logger.debug(f"CREATE: {action.reason}")

                elif action.action_type == ChangeType.UPDATE:
                    if not dry_run:
                        self._update_placeholder(
                            action.source_event,
                            action.target_event,
                            source_cal_id,
                        )
                    result.updated += 1
                    logger.debug(f"UPDATE: {action.reason}")

                elif action.action_type == ChangeType.DELETE:
                    if not dry_run:
                        self.adapter.delete_event(action.target_event.id)
                    result.deleted += 1
                    logger.debug(f"DELETE: {action.reason}")

            except Exception as e:
                error_msg = f"Error in {action.action_type.value}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        return result

    def _create_placeholder(
        self,
        source_event: CalendarEvent,
        source_cal_id: str,
        target_cal_id: str,
    ) -> None:
        """Create a placeholder for a source event."""
        tracking_id = PlaceholderInfo.generate_tracking_id()
        source_hash = self.tracker.compute_event_hash(source_event)

        notes = self.tracker.create_placeholder_notes(
            tracking_id=tracking_id,
            source_event_id=source_event.id,
            source_calendar_id=source_cal_id,
            source_hash=source_hash,
        )

        self.adapter.create_event(
            calendar_id=target_cal_id,
            title=self.PLACEHOLDER_TITLE,
            start_date=source_event.start_date,
            end_date=source_event.end_date,
            is_all_day=source_event.is_all_day,
            notes=notes,
        )

    def _update_placeholder(
        self,
        source_event: CalendarEvent,
        placeholder_event: CalendarEvent,
        source_cal_id: str,
    ) -> None:
        """Update an existing placeholder."""
        info = self.tracker.extract_tracking_info(placeholder_event)
        source_hash = self.tracker.compute_event_hash(source_event)

        notes = self.tracker.create_placeholder_notes(
            tracking_id=info.tracking_id,
            source_event_id=source_event.id,
            source_calendar_id=source_cal_id,
            source_hash=source_hash,
        )

        self.adapter.update_event(
            event_id=placeholder_event.id,
            start_date=source_event.start_date,
            end_date=source_event.end_date,
            notes=notes,
        )
