"""Calendar event data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CalendarEvent:
    """Represents a calendar event."""

    id: str
    calendar_id: str
    title: str
    start_date: datetime
    end_date: datetime
    is_all_day: bool
    notes: Optional[str] = None
    location: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        """Calculate event duration in minutes."""
        return int((self.end_date - self.start_date).total_seconds() / 60)
