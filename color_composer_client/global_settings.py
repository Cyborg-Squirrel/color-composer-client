"""
The global settings object.
"""

import json
from dataclasses import asdict, dataclass
from typing import Optional

from color_composer_client.validation_result import ValidationResult


@dataclass
class GlobalSettings:
    """Global Color Composer Client settings.

    Attributes:
        power_limit: Maximum power consumption limit in milliamps.
            A value of 0 means the power limit is disabled.
        fade_timeout_ms: Milliseconds of inactivity after the last frame before
            the renderer begins dimming LEDs to blank. None disables the feature.
    """

    power_limit: int
    fade_timeout_millis: Optional[int] = None

    def __init__(self, power_limit: int, fade_timeout_millis: Optional[int] = None):
        """Initialize global settings.

        Args:
            power_limit: Maximum power consumption limit in milliamps.
            fade_timeout_millis: Inactivity timeout in milliseconds before dimming starts.
        """
        self.power_limit = power_limit
        self.fade_timeout_millis = fade_timeout_millis

    @classmethod
    def default(cls) -> "GlobalSettings":
        """Create default global settings.

        Returns:
            GlobalSettings object with default values.
        """
        return GlobalSettings(power_limit=0, fade_timeout_millis=15000)

    def check_validity(self) -> ValidationResult:
        """Validate the global settings.

        Returns:
            ValidationResult: Object containing validity status and error message if invalid.
        """
        if not isinstance(self.power_limit, int) or self.power_limit < 0:
            return ValidationResult(
                False, "Power limit must be a non-negative integer."
            )
        if self.fade_timeout_millis is not None:
            if not isinstance(self.fade_timeout_millis, int) or self.fade_timeout_millis < 0:
                return ValidationResult(
                    False, "Fade timeout must be a non-negative integer."
                )
        return ValidationResult(True, "")

    def to_json(self) -> str:
        """Serializes these settings to json."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_dict: dict) -> "GlobalSettings":
        """Deserializes settings from json."""
        return cls(**json_dict)
