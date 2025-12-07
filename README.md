# CalSync

Bidirektionaler Kalender-Sync für macOS. Erstellt automatisch Platzhaltertermine ("Nicht verfügbar") zwischen zwei Kalendern in der Apple Kalender-App.

## Anwendungsfall

Du hast zwei Kalender (z.B. Arbeitgeber und Kunde) und möchtest, dass beide Seiten deine Verfügbarkeit sehen können, ohne die Details der Termine preiszugeben. CalSync erstellt für jeden Termin im einen Kalender einen "Nicht verfügbar"-Platzhalter im anderen Kalender.

## Installation

```bash
# Repository klonen
git clone <repo-url>
cd CalSync

# Dependencies installieren
uv sync

# Oder mit pip
pip install -e .
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

Wählt die beiden zu synchronisierenden Kalender aus. Die Konfiguration wird in `.calsync.json` im aktuellen Verzeichnis gespeichert.

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

## Funktionsweise

- Für jeden "echten" Termin in Kalender A wird ein Platzhalter in Kalender B erstellt (und umgekehrt)
- Platzhalter haben den Titel "Nicht verfügbar" und blockieren nur die Zeit
- Änderungen an Terminen (Zeit, Dauer) werden bei erneutem Sync übernommen
- Gelöschte Termine führen zur Löschung des zugehörigen Platzhalters
- Platzhalter werden über eine versteckte ID im Notizen-Feld getrackt

## Voraussetzungen

- macOS (getestet mit macOS Sequoia)
- Python 3.12+
- Kalenderzugriff muss beim ersten Start gewährt werden

## Technologie

- [PyObjC](https://pyobjc.readthedocs.io/) mit EventKit Framework für nativen Kalenderzugriff
- [Click](https://click.palletsprojects.com/) für die CLI

## Lizenz

MIT License - siehe [LICENSE.md](LICENSE.md)
