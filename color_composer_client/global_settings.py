"""
The global settings object.
"""

import json
from dataclasses import asdict, dataclass

from color_composer_client.validation_result import ValidationResult


@dataclass
class GlobalSettings:
    """Global Color Composer Client settings.
    
    Attributes:
        power_limit: Maximum power consumption limit in milliamps.
        A value of 0 means the power limit is disabled.
    """

    power_limit: int

    def __init__(self, power_limit: int):
        """Initialize global settings.
        
        Args:
            power_limit: Maximum power consumption limit in milliamps.
        """
        self.power_limit = power_limit

    @classmethod
    def default(cls) -> "GlobalSettings":
        """Create default global settings.
        
        Returns:
            GlobalSettings object with default values.
        """
        return GlobalSettings(power_limit=0)

    def check_validity(self) -> ValidationResult:
        """Validate the global settings.
        
        Returns:
            ValidationResult: Object containing validity status and error message if invalid.
        """
        if not isinstance(self.power_limit, int) or self.power_limit < 0:
            return ValidationResult(
                False, "Power limit must be a non-negative integer."
            )
        return ValidationResult(True, "")

    def to_json(self) -> str:
        """Serializes these settings to json."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_dict: dict) -> "GlobalSettings":
        """Deserializes settings from json."""
        return cls(**json_dict)
