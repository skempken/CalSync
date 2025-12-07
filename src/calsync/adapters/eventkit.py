"""EventKit-based calendar adapter for macOS."""

import threading
from datetime import datetime
from typing import Optional

from EventKit import (
    EKEntityTypeEvent,
    EKEvent,
    EKEventStore,
    EKSpanThisEvent,
)
from Foundation import NSDate

from calsync.adapters.base import CalendarAdapter
from calsync.models.event import CalendarEvent


class EventKitAdapter(CalendarAdapter):
    """EventKit-based adapter for Apple Calendar on macOS."""

    def __init__(self):
        self._store: Optional[EKEventStore] = None
        self._authorized: bool = False

    @property
    def store(self) -> EKEventStore:
        """Lazy initialization of the event store with authorization."""
        if self._store is None:
            self._store = EKEventStore.alloc().init()
            self._request_authorization()
        return self._store

    def _request_authorization(self) -> None:
        """Request calendar access (blocking)."""
        event = threading.Event()
        result = {"granted": False, "error": None}

        def callback(granted, error):
            result["granted"] = granted
            result["error"] = error
            event.set()

        self._store.requestFullAccessToEventsWithCompletion_(callback)
        event.wait(timeout=30)

        if not result["granted"]:
            raise PermissionError(
                f"Calendar access denied: {result['error']}"
            )
        self._authorized = True

    def _nsdate_from_datetime(self, dt: datetime) -> NSDate:
        """Convert Python datetime to NSDate."""
        return NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())

    def _datetime_from_nsdate(self, nsdate: NSDate) -> datetime:
        """Convert NSDate to Python datetime."""
        return datetime.fromtimestamp(nsdate.timeIntervalSince1970())

    def _event_to_model(self, ek_event: EKEvent) -> CalendarEvent:
        """Convert EKEvent to CalendarEvent model."""
        return CalendarEvent(
            id=ek_event.eventIdentifier(),
            calendar_id=ek_event.calendar().calendarIdentifier(),
            title=ek_event.title() or "",
            start_date=self._datetime_from_nsdate(ek_event.startDate()),
            end_date=self._datetime_from_nsdate(ek_event.endDate()),
            is_all_day=ek_event.isAllDay(),
            notes=ek_event.notes(),
            location=ek_event.location(),
        )

    def get_calendars(self) -> list[dict]:
        """List all calendars."""
        calendars = self.store.calendarsForEntityType_(EKEntityTypeEvent)
        return [
            {
                "id": cal.calendarIdentifier(),
                "name": cal.title(),
                "source": cal.source().title() if cal.source() else None,
                "writable": cal.allowsContentModifications(),
            }
            for cal in calendars
        ]

    def get_events(
        self,
        calendar_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Get events from a calendar within a time range."""
        calendar = self.store.calendarWithIdentifier_(calendar_id)
        if not calendar:
            raise ValueError(f"Calendar not found: {calendar_id}")

        ns_start = self._nsdate_from_datetime(start_date)
        ns_end = self._nsdate_from_datetime(end_date)

        predicate = self.store.predicateForEventsWithStartDate_endDate_calendars_(
            ns_start, ns_end, [calendar]
        )

        ek_events = self.store.eventsMatchingPredicate_(predicate)
        return [self._event_to_model(ev) for ev in (ek_events or [])]

    def get_event_by_id(self, event_id: str) -> Optional[CalendarEvent]:
        """Get a single event by ID."""
        ek_event = self.store.eventWithIdentifier_(event_id)
        if ek_event:
            return self._event_to_model(ek_event)
        return None

    def create_event(
        self,
        calendar_id: str,
        title: str,
        start_date: datetime,
        end_date: datetime,
        is_all_day: bool = False,
        notes: Optional[str] = None,
    ) -> CalendarEvent:
        """Create a new event."""
        calendar = self.store.calendarWithIdentifier_(calendar_id)
        if not calendar:
            raise ValueError(f"Calendar not found: {calendar_id}")

        if not calendar.allowsContentModifications():
            raise PermissionError(f"Calendar is read-only: {calendar.title()}")

        # Important: Use eventWithEventStore_ instead of alloc().init()
        event = EKEvent.eventWithEventStore_(self.store)
        event.setTitle_(title)
        event.setCalendar_(calendar)
        event.setStartDate_(self._nsdate_from_datetime(start_date))
        event.setEndDate_(self._nsdate_from_datetime(end_date))
        event.setAllDay_(is_all_day)

        if notes:
            event.setNotes_(notes)

        success, error = self.store.saveEvent_span_error_(
            event, EKSpanThisEvent, None
        )

        if not success:
            raise RuntimeError(f"Failed to create event: {error}")

        return self._event_to_model(event)

    def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> CalendarEvent:
        """Update an existing event."""
        ek_event = self.store.eventWithIdentifier_(event_id)
        if not ek_event:
            raise ValueError(f"Event not found: {event_id}")

        if title is not None:
            ek_event.setTitle_(title)
        if start_date is not None:
            ek_event.setStartDate_(self._nsdate_from_datetime(start_date))
        if end_date is not None:
            ek_event.setEndDate_(self._nsdate_from_datetime(end_date))
        if notes is not None:
            ek_event.setNotes_(notes)

        success, error = self.store.saveEvent_span_error_(
            ek_event, EKSpanThisEvent, None
        )

        if not success:
            raise RuntimeError(f"Failed to update event: {error}")

        return self._event_to_model(ek_event)

    def delete_event(self, event_id: str) -> bool:
        """Delete an event."""
        ek_event = self.store.eventWithIdentifier_(event_id)
        if not ek_event:
            return False

        success, error = self.store.removeEvent_span_error_(
            ek_event, EKSpanThisEvent, None
        )

        return success
