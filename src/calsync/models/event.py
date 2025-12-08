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
    # EventKit availability: 0=Busy, 1=Free, 2=Tentative, 3=Unavailable
    availability: Optional[int] = None
    # EventKit self participant status: 1=Pending, 2=Accepted, 3=Declined, 4=Tentative
    self_participant_status: Optional[int] = None

    @property
    def duration_minutes(self) -> int:
        """Calculate event duration in minutes."""
        return int((self.end_date - self.start_date).total_seconds() / 60)
