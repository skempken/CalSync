# CalSync - Projektanweisungen

## Überblick

CalSync ist ein macOS CLI-Tool zur Synchronisierung von Platzhalterterminen zwischen mehreren Kalendern in der Apple Kalender-App. Es verwendet PyObjC mit dem EventKit Framework.

## Projektstruktur

```
src/calsync/
├── cli.py              # Click CLI Commands
├── config.py           # Konfiguration & Profile
├── adapters/
│   ├── base.py         # Abstract CalendarAdapter
│   └── eventkit.py     # PyObjC EventKit Implementation
├── models/
│   ├── event.py        # CalendarEvent Dataclass
│   └── placeholder.py  # Tracking-ID Logik (Notes-Feld)
└── sync/
    ├── engine.py       # SyncEngine (Orchestrierung)
    ├── tracker.py      # Event-Hash & Tracking
    └── differ.py       # Change Detection & Filterung
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

# Mit Profil (für verschiedene Konfigurationen)
uv run calsync -p <profil> <command>
```

## Profile

Profile ermöglichen verschiedene Sync-Konfigurationen:

| Profil | Config-Datei |
|--------|--------------|
| (default) | `.calsync.json` |
| test | `.calsync-test.json` |
| prod | `.calsync-prod.json` |

```bash
# Profil konfigurieren
uv run calsync -p test configure

# Status eines Profils anzeigen
uv run calsync -p test status

# Sync mit Profil
uv run calsync -p test sync --dry-run
```

## Annahmestatus & Verfügbarkeit

Der Annahmestatus und die Verfügbarkeit von Terminen werden berücksichtigt:

| Quelltermin | Platzhalter |
|-------------|-------------|
| Außer Haus (Out of Office) | Außer Haus |
| Tentative (unter Vorbehalt) | Tentative |
| Accepted (angenommen) | Busy |
| Free (frei) | Nicht synchronisiert |
| Pending (nicht beantwortet) | Nicht synchronisiert |
| Declined (abgelehnt) | Nicht synchronisiert |

Priorität: Außer Haus > Tentative > Busy

EventKit-Details siehe `notes.md`.

## Architektur

- **Adapter-Schicht**: Abstrahiert Kalenderzugriff (aktuell nur EventKit)
- **Sync-Logik**: Engine orchestriert, Differ erkennt Änderungen, Tracker verwaltet IDs
- **Tracking**: Platzhalter werden über JSON-Marker im Notes-Feld identifiziert: `[CALSYNC:{"tid":"...","src":"...","scal":"...","hash":"...","sstart":"..."}]`
- **Wiederkehrende Termine**: Jedes Vorkommen wird separat getrackt via `event_id + start_date`
- **Status-Handling**: `selfParticipantStatus()` vom Quelltermin → `availability` beim Platzhalter

## Wichtige Hinweise

- Kalenderzugriff erfordert macOS-Berechtigung (wird beim ersten Start angefordert)
- Konfigurationen liegen lokal (`.calsync*.json`) - nicht committen
- Test-Kalender: "Arbeitgeber", "Kunde" (iCloud)
- Platzhalter-Titel: "Nicht verfügbar"

## Tests

Manuelle Tests gegen echte Kalender. Für Tests ein separates Profil verwenden:

```bash
# Test-Profil mit Arbeitgeber/Kunde konfigurieren
uv run calsync -p test configure

# Dry-Run zum Testen
uv run calsync -p test sync --dry-run --days 7

# Nach Tests: Platzhalter in Test-Kalendern manuell löschen
```
