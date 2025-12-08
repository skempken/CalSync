"""Change detection between calendars."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from calsync.models.event import CalendarEvent
from calsync.sync.tracker import EventTracker

# EventKit participant status constants
PARTICIPANT_STATUS_PENDING = 1
PARTICIPANT_STATUS_ACCEPTED = 2
PARTICIPANT_STATUS_DECLINED = 3
PARTICIPANT_STATUS_TENTATIVE = 4

# EventKit availability constants
AVAILABILITY_FREE = 1


class ChangeType(Enum):
    """Type of sync action."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NOOP = "noop"


@dataclass
class SyncAction:
    """Describes a sync action to perform."""

    action_type: ChangeType
    source_event: Optional[CalendarEvent]
    target_event: Optional[CalendarEvent]
    reason: str


class ChangeDiffer:
    """Determines necessary sync actions between two calendars."""

    def __init__(self, tracker: EventTracker):
        self.tracker = tracker

    def _should_sync_event(self, event: CalendarEvent) -> bool:
        """
        Check if an event should be synced.

        Excludes:
        - Placeholders (already synced)
        - Pending events (not yet responded)
        - Declined events
        - Free events (no time blocking)
        """
        if self.tracker.is_placeholder(event):
            return False

        # Skip free events (availability = 1)
        if event.availability == AVAILABILITY_FREE:
            return False

        status = event.self_participant_status
        # Skip pending (1) and declined (3) events
        if status == PARTICIPANT_STATUS_PENDING:
            return False
        if status == PARTICIPANT_STATUS_DECLINED:
            return False

        return True

    def compute_sync_actions(
        self,
        source_events: list[CalendarEvent],
        target_events: list[CalendarEvent],
        source_calendar_id: str,
    ) -> list[SyncAction]:
        """
        Compute all necessary sync actions.

        Args:
            source_events: Events from source calendar
            target_events: Events from target calendar (including placeholders)
            source_calendar_id: ID of the source calendar

        Returns:
            List of SyncActions to perform
        """
        actions: list[SyncAction] = []

        # Filter: Only syncable events (not placeholders, not pending/declined)
        real_source_events = [
            e for e in source_events if self._should_sync_event(e)
        ]

        # Find placeholders in target calendar that originated from source
        # Use occurrence key (event_id + start_date) to handle recurring events
        placeholders: dict[str, CalendarEvent] = {}
        for event in target_events:
            if self.tracker.is_placeholder(event):
                info = self.tracker.extract_tracking_info(event)
                if info and info.source_calendar_id == source_calendar_id:
                    placeholders[info.get_occurrence_key()] = event

        # 1. CREATE/UPDATE: Check each source event
        for source in real_source_events:
            occurrence_key = self.tracker.get_occurrence_key(source)
            if occurrence_key in placeholders:
                # Placeholder exists - check if update needed
                placeholder = placeholders[occurrence_key]
                info = self.tracker.extract_tracking_info(placeholder)
                current_hash = self.tracker.compute_event_hash(source)

                if info and info.source_hash != current_hash:
                    actions.append(
                        SyncAction(
                            action_type=ChangeType.UPDATE,
                            source_event=source,
                            target_event=placeholder,
                            reason=f"Event changed (hash: {info.source_hash[:8]} -> {current_hash[:8]})",
                        )
                    )
            else:
                # New placeholder needed
                actions.append(
                    SyncAction(
                        action_type=ChangeType.CREATE,
                        source_event=source,
                        target_event=None,
                        reason="New event, creating placeholder",
                    )
                )

        # 2. DELETE: Remove placeholders without source event
        source_keys = {self.tracker.get_occurrence_key(e) for e in real_source_events}
        for occurrence_key, placeholder in placeholders.items():
            if occurrence_key not in source_keys:
                actions.append(
                    SyncAction(
                        action_type=ChangeType.DELETE,
                        source_event=None,
                        target_event=placeholder,
                        reason="Source event deleted, removing placeholder",
                    )
                )

        return actions
