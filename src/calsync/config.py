"""Configuration management for CalSync."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CONFIG_FILE = Path.cwd() / ".calsync.json"


@dataclass
class Config:
    """Application configuration."""

    calendar_a_id: Optional[str] = None
    calendar_a_name: Optional[str] = None
    calendar_b_id: Optional[str] = None
    calendar_b_name: Optional[str] = None

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file."""
        if not CONFIG_FILE.exists():
            return cls()

        with open(CONFIG_FILE) as f:
            data = json.load(f)
        return cls(**data)

    def save(self) -> None:
        """Save configuration to file."""
        with open(CONFIG_FILE, "w") as f:
            json.dump(
                {
                    "calendar_a_id": self.calendar_a_id,
                    "calendar_a_name": self.calendar_a_name,
                    "calendar_b_id": self.calendar_b_id,
                    "calendar_b_name": self.calendar_b_name,
                },
                f,
                indent=2,
            )

    def is_configured(self) -> bool:
        """Check if both calendars are configured."""
        return bool(self.calendar_a_id and self.calendar_b_id)
