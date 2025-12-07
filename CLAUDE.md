# CalSync - Projektanweisungen

## Überblick

CalSync ist ein macOS CLI-Tool zur Synchronisierung von Platzhalterterminen zwischen mehreren Kalendern in der Apple Kalender-App. Es verwendet PyObjC mit dem EventKit Framework.

## Projektstruktur

```
src/calsync/
├── cli.py              # Click CLI Commands
├── config.py           # Konfiguration (.calsync.json)
├── adapters/
│   ├── base.py         # Abstract CalendarAdapter
│   └── eventkit.py     # PyObjC EventKit Implementation
├── models/
│   ├── event.py        # CalendarEvent Dataclass
│   └── placeholder.py  # Tracking-ID Logik (Notes-Feld)
└── sync/
    ├── engine.py       # SyncEngine (Orchestrierung)
    ├── tracker.py      # Event-Hash & Tracking
    └── differ.py       # Change Detection
```

## Entwicklung

```bash
# Dependencies installieren
uv sync

# CLI ausführen
uv run calsync <command>

# Verfügbare Commands
uv run calsync list-calendars
uv run calsync configure
uv run calsync status
uv run calsync sync [--dry-run] [--days N]
```

## Architektur

- **Adapter-Schicht**: Abstrahiert Kalenderzugriff (aktuell nur EventKit)
- **Sync-Logik**: Engine orchestriert, Differ erkennt Änderungen, Tracker verwaltet IDs
- **Tracking**: Platzhalter werden über JSON-Marker im Notes-Feld identifiziert: `[CALSYNC:{"tid":"...","src":"...","scal":"...","hash":"..."}]`

## Wichtige Hinweise

- Kalenderzugriff erfordert macOS-Berechtigung (wird beim ersten Start angefordert)
- Konfiguration liegt lokal in `.calsync.json` (nicht committen)
- Test-Kalender: "Arbeitgeber", "Kunde", "Privat" (iCloud)
- Platzhalter-Titel: "Nicht verfügbar"

## Tests

Manuelle Tests gegen echte Kalender. Testtermine nach dem Testen löschen.
