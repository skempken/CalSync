"""Main sync engine."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from calsync.adapters.base import CalendarAdapter
from calsync.models.event import CalendarEvent
from calsync.models.placeholder import PlaceholderInfo
from calsync.sync.differ import ChangeDiffer, ChangeType, SyncAction
from calsync.sync.tracker import EventTracker

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a sync operation."""

    created: int = 0
    updated: int = 0
    deleted: int = 0
    errors: list[str] = field(default_factory=list)


class SyncEngine:
    """Main sync logic for bidirectional calendar sync."""

    PLACEHOLDER_TITLE = "Nicht verfügbar"

    def __init__(
        self,
        adapter: CalendarAdapter,
        calendar_a_id: str,
        calendar_b_id: str,
    ):
        self.adapter = adapter
        self.calendar_a_id = calendar_a_id
        self.calendar_b_id = calendar_b_id
        self.tracker = EventTracker()
        self.differ = ChangeDiffer(self.tracker)

    def sync(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        dry_run: bool = False,
    ) -> tuple[SyncResult, SyncResult]:
        """
        Perform bidirectional sync.

        Args:
            start_date: Start of sync period (default: today)
            end_date: End of sync period (default: +30 days)
            dry_run: If True, only simulate changes

        Returns:
            Tuple of SyncResults (A->B, B->A)
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if end_date is None:
            end_date = start_date + timedelta(days=30)

        logger.info(f"Sync period: {start_date.date()} to {end_date.date()}")

        # Get events from both calendars
        events_a = self.adapter.get_events(self.calendar_a_id, start_date, end_date)
        events_b = self.adapter.get_events(self.calendar_b_id, start_date, end_date)

        logger.info(f"Calendar A: {len(events_a)} events")
        logger.info(f"Calendar B: {len(events_b)} events")

        # Sync A -> B
        result_a_to_b = self._sync_direction(
            events_a,
            events_b,
            self.calendar_a_id,
            self.calendar_b_id,
            dry_run,
        )

        # Refresh events_a after A->B sync (new placeholders may have been created)
        if not dry_run:
            events_a = self.adapter.get_events(self.calendar_a_id, start_date, end_date)

        # Sync B -> A
        result_b_to_a = self._sync_direction(
            events_b,
            events_a,
            self.calendar_b_id,
            self.calendar_a_id,
            dry_run,
        )

        return result_a_to_b, result_b_to_a

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

        logger.info(f"Direction {source_cal_id[:8]}... -> {target_cal_id[:8]}...: {len(actions)} actions")

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
                    logger.info(f"CREATE: {action.reason}")

                elif action.action_type == ChangeType.UPDATE:
                    if not dry_run:
                        self._update_placeholder(
                            action.source_event,
                            action.target_event,
                            source_cal_id,
                        )
                    result.updated += 1
                    logger.info(f"UPDATE: {action.reason}")

                elif action.action_type == ChangeType.DELETE:
                    if not dry_run:
                        self.adapter.delete_event(action.target_event.id)
                    result.deleted += 1
                    logger.info(f"DELETE: {action.reason}")

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
