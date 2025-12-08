"""Abstract base class for calendar adapters."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from calsync.models.event import CalendarEvent


class CalendarAdapter(ABC):
    """Abstract base class for calendar adapters."""

    @abstractmethod
    def get_calendars(self) -> list[dict]:
        """List all available calendars.

        Returns:
            List of calendar info dicts with keys:
            - id: Calendar identifier
            - name: Calendar title
            - source: Source name (e.g. "iCloud", "Exchange")
            - writable: Whether calendar allows modifications
        """
        pass

    @abstractmethod
    def get_events(
        self,
        calendar_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Get events from a calendar within a time range."""
        pass

    @abstractmethod
    def get_event_by_id(self, event_id: str) -> Optional[CalendarEvent]:
        """Get a single event by ID."""
        pass

    @abstractmethod
    def create_event(
        self,
        calendar_id: str,
        title: str,
        start_date: datetime,
        end_date: datetime,
        is_all_day: bool = False,
        notes: Optional[str] = None,
        availability: Optional[int] = None,
    ) -> CalendarEvent:
        """Create a new event."""
        pass

    @abstractmethod
    def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        notes: Optional[str] = None,
        availability: Optional[int] = None,
    ) -> CalendarEvent:
        """Update an existing event."""
        pass

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete an event. Returns True if successful."""
        pass
