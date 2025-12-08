# CalSync

Multi-Kalender-Sync für macOS. Erstellt automatisch Platzhaltertermine ("Nicht verfügbar") zwischen beliebig vielen Kalendern in der Apple Kalender-App.

## Anwendungsfall

Du hast mehrere Kalender (z.B. Arbeitgeber, Kunde, Privat) und möchtest, dass alle Seiten deine Verfügbarkeit sehen können, ohne die Details der Termine preiszugeben. CalSync erstellt für jeden Termin in einem Kalender einen "Nicht verfügbar"-Platzhalter in allen anderen konfigurierten Kalendern.

## Installation

```bash
# Repository klonen
git clone https://github.com/skempken/CalSync.git
cd CalSync

# Dependencies installieren
uv sync
```

## Verwendung

### Kalender auflisten

```bash
uv run calsync list-calendars
```

Zeigt alle verfügbaren Kalender mit ID und Schreibrechten an.

### Kalender konfigurieren

```bash
uv run calsync configure
```

Wählt die zu synchronisierenden Kalender aus (mind. 2, beliebig viele möglich). Die Konfiguration wird in `.calsync.json` im aktuellen Verzeichnis gespeichert.

### Konfiguration anzeigen

```bash
uv run calsync status
```

### Synchronisieren

```bash
# Sync durchführen (Standard: nächste 30 Tage)
uv run calsync sync

# Nur simulieren (keine Änderungen)
uv run calsync sync --dry-run

# Anderen Zeitraum wählen
uv run calsync sync --days 60

# Mit detaillierter Ausgabe
uv run calsync -v sync
```

### Profile (für verschiedene Konfigurationen)

```bash
# Separates Profil konfigurieren
uv run calsync -p work configure

# Sync mit Profil
uv run calsync -p work sync
```

Profile werden als `.calsync-<name>.json` gespeichert.

## Funktionsweise

- Für jeden "echten" Termin in einem Kalender wird ein Platzhalter in allen anderen konfigurierten Kalendern erstellt
- Bei n Kalendern werden n-1 Platzhalter pro Termin erstellt
- Platzhalter haben den Titel "Nicht verfügbar" und blockieren nur die Zeit
- Änderungen an Terminen (Zeit, Dauer) werden bei erneutem Sync übernommen
- Gelöschte Termine führen zur Löschung der zugehörigen Platzhalter
- Platzhalter werden über eine versteckte ID im Notizen-Feld getrackt

### Annahmestatus & Verfügbarkeit

Der Annahmestatus von Einladungen wird auf Platzhalter übertragen:

| Quelltermin | Platzhalter |
|-------------|-------------|
| Außer Haus (Out of Office) | Außer Haus |
| Unter Vorbehalt (Tentative) | Unter Vorbehalt |
| Angenommen (Accepted) | Belegt |
| Nicht beantwortet (Pending) | *nicht synchronisiert* |
| Abgelehnt (Declined) | *nicht synchronisiert* |

## Voraussetzungen

- macOS (getestet mit macOS Tahoe)
- Python 3.12+
- Kalenderzugriff muss beim ersten Start gewährt werden

## Technologie

- [PyObjC](https://pyobjc.readthedocs.io/) mit EventKit Framework für nativen Kalenderzugriff
- [Click](https://click.palletsprojects.com/) für die CLI

## Lizenz

MIT License - siehe [LICENSE.md](LICENSE.md)
