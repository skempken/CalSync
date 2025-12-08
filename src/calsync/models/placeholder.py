"""Placeholder tracking logic."""

import json
import uuid
from dataclasses import dataclass
from typing import Optional

TRACKING_PREFIX = "[CALSYNC:"
TRACKING_SUFFIX = "]"


@dataclass
class PlaceholderInfo:
    """Information stored in placeholder notes field."""

    tracking_id: str
    source_event_id: str
    source_calendar_id: str
    source_hash: str
    source_start: Optional[str] = None  # ISO format, for recurring events

    @staticmethod
    def generate_tracking_id() -> str:
        """Generate a new tracking ID."""
        return str(uuid.uuid4())[:8]

    def get_occurrence_key(self) -> str:
        """Get unique key for this occurrence (handles recurring events)."""
        if self.source_start:
            return f"{self.source_event_id}_{self.source_start}"
        return self.source_event_id

    def to_notes_marker(self) -> str:
        """Create the tracking marker for the notes field."""
        data = {
            "tid": self.tracking_id,
            "src": self.source_event_id,
            "scal": self.source_calendar_id,
            "hash": self.source_hash,
        }
        if self.source_start:
            data["sstart"] = self.source_start
        return f"{TRACKING_PREFIX}{json.dumps(data)}{TRACKING_SUFFIX}"

    @classmethod
    def from_notes(cls, notes: Optional[str]) -> Optional["PlaceholderInfo"]:
        """Extract tracking info from notes field."""
        if not notes or TRACKING_PREFIX not in notes:
            return None
        try:
            start = notes.index(TRACKING_PREFIX) + len(TRACKING_PREFIX)
            end = notes.index(TRACKING_SUFFIX, start)
            data = json.loads(notes[start:end])
            return cls(
                tracking_id=data["tid"],
                source_event_id=data["src"],
                source_calendar_id=data["scal"],
                source_hash=data["hash"],
                source_start=data.get("sstart"),  # Optional for backwards compat
            )
        except (ValueError, json.JSONDecodeError, KeyError):
            return None
