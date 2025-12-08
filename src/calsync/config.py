"""Configuration management for CalSync."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.cwd()


def get_config_file(profile: Optional[str] = None) -> Path:
    """Get config file path for a profile."""
    if profile:
        return CONFIG_DIR / f".calsync-{profile}.json"
    return CONFIG_DIR / ".calsync.json"


@dataclass
class CalendarConfig:
    """Configuration for a single calendar."""

    id: str
    name: str


@dataclass
class Config:
    """Application configuration."""

    calendars: list[CalendarConfig] = field(default_factory=list)
    profile: Optional[str] = None

    @classmethod
    def load(cls, profile: Optional[str] = None) -> "Config":
        """Load configuration from file."""
        config_file = get_config_file(profile)
        if not config_file.exists():
            return cls(profile=profile)

        with open(config_file) as f:
            data = json.load(f)

        # Handle legacy format (calendar_a_id, calendar_b_id)
        if "calendar_a_id" in data:
            calendars = []
            if data.get("calendar_a_id"):
                calendars.append(
                    CalendarConfig(
                        id=data["calendar_a_id"],
                        name=data.get("calendar_a_name", "Calendar A"),
                    )
                )
            if data.get("calendar_b_id"):
                calendars.append(
                    CalendarConfig(
                        id=data["calendar_b_id"],
                        name=data.get("calendar_b_name", "Calendar B"),
                    )
                )
            return cls(calendars=calendars, profile=profile)

        # New format
        calendars = [CalendarConfig(**c) for c in data.get("calendars", [])]
        return cls(calendars=calendars, profile=profile)

    def save(self) -> None:
        """Save configuration to file."""
        config_file = get_config_file(self.profile)
        with open(config_file, "w") as f:
            json.dump(
                {"calendars": [{"id": c.id, "name": c.name} for c in self.calendars]},
                f,
                indent=2,
            )

    def is_configured(self) -> bool:
        """Check if at least two calendars are configured."""
        return len(self.calendars) >= 2

    def get_calendar_ids(self) -> list[str]:
        """Get list of calendar IDs."""
        return [c.id for c in self.calendars]

    def get_calendar_name(self, calendar_id: str) -> str:
        """Get calendar name by ID."""
        for c in self.calendars:
            if c.id == calendar_id:
                return c.name
        return calendar_id[:8]
