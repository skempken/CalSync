"""Change detection between calendars."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from calsync.models.event import CalendarEvent
from calsync.sync.tracker import EventTracker


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

        # Filter: Only "real" events (not placeholders) from source
        real_source_events = [
            e for e in source_events if not self.tracker.is_placeholder(e)
        ]

        # Find placeholders in target calendar that originated from source
        placeholders: dict[str, CalendarEvent] = {}
        for event in target_events:
            if self.tracker.is_placeholder(event):
                info = self.tracker.extract_tracking_info(event)
                if info and info.source_calendar_id == source_calendar_id:
                    placeholders[info.source_event_id] = event

        # 1. CREATE/UPDATE: Check each source event
        for source in real_source_events:
            if source.id in placeholders:
                # Placeholder exists - check if update needed
                placeholder = placeholders[source.id]
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
        source_ids = {e.id for e in real_source_events}
        for source_id, placeholder in placeholders.items():
            if source_id not in source_ids:
                actions.append(
                    SyncAction(
                        action_type=ChangeType.DELETE,
                        source_event=None,
                        target_event=placeholder,
                        reason="Source event deleted, removing placeholder",
                    )
                )

        return actions
