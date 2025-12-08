# EventKit: Annahmestatus und Verfügbarkeit

## Zwei verschiedene Konzepte

### 1. Participant Status (für Einladungen)
Dein Status als Teilnehmer bei Events, zu denen du eingeladen wurdest.

**Methode:** `event.selfParticipantStatus()`

| Wert | Konstante | Bedeutung |
|------|-----------|-----------|
| 1 | `EKParticipantStatusPending` | Noch nicht geantwortet |
| 2 | `EKParticipantStatusAccepted` | Angenommen |
| 3 | `EKParticipantStatusDeclined` | Abgelehnt |
| 4 | `EKParticipantStatusTentative` | Unter Vorbehalt |

**Wichtig:** Dieser Status ist **read-only** - er wird von der Kalender-App gesetzt, wenn du auf eine Einladung antwortest.

### 2. Event Availability (für eigene Events)
Verfügbarkeit, die bei selbst erstellten Events gesetzt werden kann.

**Methode:** `event.setAvailability_(value)`

| Wert | Konstante | Bedeutung |
|------|-----------|-----------|
| 0 | `EKEventAvailabilityBusy` | Belegt |
| 1 | `EKEventAvailabilityFree` | Frei |
| 2 | `EKEventAvailabilityTentative` | Unter Vorbehalt |
| 3 | `EKEventAvailabilityUnavailable` | Nicht verfügbar |
| -1 | (kein Wert) | Nicht gesetzt |

**Wichtig:** Diese Property kann bei Events gesetzt werden, die wir selbst erstellen.

## PyObjC Code-Beispiele

### Participant Status lesen
```python
from EventKit import (
    EKParticipantStatusAccepted,
    EKParticipantStatusTentative,
    EKParticipantStatusPending,
    EKParticipantStatusDeclined,
)

status = event.selfParticipantStatus()

if status == EKParticipantStatusTentative:
    print("Unter Vorbehalt angenommen")
elif status == EKParticipantStatusAccepted:
    print("Angenommen")
elif status == EKParticipantStatusPending:
    print("Noch nicht geantwortet")
elif status == EKParticipantStatusDeclined:
    print("Abgelehnt")
```

### Availability setzen
```python
from EventKit import (
    EKEventAvailabilityBusy,
    EKEventAvailabilityTentative,
)

# Bei neuem Event
event = EKEvent.eventWithEventStore_(store)
event.setTitle_("Platzhalter")
event.setAvailability_(EKEventAvailabilityTentative)

# Event speichern
store.saveEvent_span_error_(event, EKSpanThisEvent, None)
```

### Alle Teilnehmer auslesen
```python
attendees = event.attendees()
if attendees:
    for attendee in attendees:
        name = attendee.name()
        status = attendee.participantStatus()
        is_me = attendee.isCurrentUser()
        print(f"{name}: Status={status}, Bin ich={is_me}")
```

## Visuelle Darstellung in Apple Kalender

- **Busy (0):** Normaler, solider Balken
- **Tentative (2):** Schraffiert/gestreiftes Muster oder reduzierte Deckkraft
- **Free (1):** Erscheint transparent oder mit "Frei"-Markierung
- **Unavailable (3):** "Außer Haus" / Out of Office - spezieller OOO-Status

## CalSync-Implementierung

Für CalSync bedeutet das:

1. **Lesen:** `availability()` und `selfParticipantStatus()` vom Quelltermin
2. **Mapping (mit Priorität):**
   - Availability Free (1) → Nicht synchronisieren
   - Availability Unavailable (3) → Availability Unavailable (3) [Außer Haus]
   - Participant Tentative (4) → Availability Tentative (2)
   - Participant Accepted (2) → Availability Busy (0)
   - Participant Pending (1) → Nicht synchronisieren
   - Participant Declined (3) → Nicht synchronisieren
3. **Schreiben:** `setAvailability_()` beim Platzhalter-Event
