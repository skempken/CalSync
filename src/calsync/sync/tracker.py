"""Event tracking and hash computation."""

import hashlib
import json

from calsync.models.event import CalendarEvent
from calsync.models.placeholder import PlaceholderInfo, TRACKING_PREFIX


class EventTracker:
    """Manages tracking IDs and event hashing."""

    @staticmethod
    def compute_event_hash(event: CalendarEvent) -> str:
        """
        Compute a hash based on sync-relevant attributes.
        Used to detect changes in source events.
        """
        data = {
            "start": event.start_date.isoformat(),
            "end": event.end_date.isoformat(),
            "all_day": event.is_all_day,
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:16]

    @staticmethod
    def is_placeholder(event: CalendarEvent) -> bool:
        """Check if an event is a sync placeholder."""
        return event.notes is not None and TRACKING_PREFIX in event.notes

    @staticmethod
    def extract_tracking_info(event: CalendarEvent) -> PlaceholderInfo | None:
        """Extract tracking info from a placeholder event."""
        return PlaceholderInfo.from_notes(event.notes)

    @staticmethod
    def create_placeholder_notes(
        tracking_id: str,
        source_event_id: str,
        source_calendar_id: str,
        source_hash: str,
    ) -> str:
        """Create notes content for a placeholder."""
        info = PlaceholderInfo(
            tracking_id=tracking_id,
            source_event_id=source_event_id,
            source_calendar_id=source_calendar_id,
            source_hash=source_hash,
        )
        return info.to_notes_marker()
