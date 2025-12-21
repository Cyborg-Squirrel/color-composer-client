"""
The NeoPixel config object.
"""

# pylint: disable=too-many-positional-arguments, too-many-arguments

import json

from validation_result import ValidationResult


class NeoPixelConfig:
    """Configuration for a NeoPixel LED strip.
    
    Attributes:
        uuid: Server-assigned unique identifier for the LED strip.
        pin: GPIO pin number connected to the LED strip.
        leds: Total number of individual LEDs in the strip.
        brightness: LED brightness level from 0 to 100.
        color_order: LED color order format (e.g., 'RGB', 'GRB', 'BGR').
    """

    uuid: str
    pin: str
    leds: int
    brightness: int
    color_order: str

    def __init__(
        self, uuid: str, pin: str, leds: int, brightness: int, color_order: str
    ):
        """Initialize a NeoPixel configuration.
        
        Args:
            uuid: Server-assigned unique identifier for the LED strip.
            pin: GPIO pin number for the strip's data line.
            leds: Number of LEDs in the strip.
            brightness: Brightness level (0-100).
            color_order: Color channel order (RGB, GRB, etc).
        """
        self.uuid = uuid
        self.pin = pin
        self.leds = leds
        self.brightness = brightness
        self.color_order = color_order

    def check_validity(self) -> ValidationResult:
        """Validate the NeoPixel configuration.
        
        Returns:
            ValidationResult: Object containing validity status and error message if invalid.
        """
        if self.uuid.isspace() or len(self.uuid) == 0:
            return ValidationResult(False, "LED strip id must be non-blank")
        if self.leds < 1:
            return ValidationResult(
                False, "LED strip " + self.uuid + " must have more than 0 LEDs."
            )
        if self.brightness < 0 or self.brightness > 100:
            return ValidationResult(
                False,
                "LED strip "
                + self.uuid
                + " must have a brightness value between 0 and 100.",
            )
        if (
            not self.pin == "D10"
            and not self.pin == "D12"
            and not self.pin == "D18"
            and not self.pin == "D21"
        ):
            return ValidationResult(
                False,
                "LED strip "
                + self.uuid
                + " must be assined to pin D10, D12, D18 or D21",
            )
        if (
            not len(self.color_order) == 3
            or not "R" in self.color_order
            or not "G" in self.color_order
            or not "B" in self.color_order
        ):
            return ValidationResult(
                False,
                "Color order "
                + self.color_order
                + " is invalid. Must be RGB, GRB, or another 3 letter combination.",
            )
        return ValidationResult(True, "")

    def to_json(self) -> str:
        """Serializes this config to json."""
        return json.dumps(
            {
                "uuid": self.uuid,
                "pin": self.pin,
                "leds": self.leds,
                "brightness": self.brightness,
            }
        )


def from_json(json_dict: dict) -> NeoPixelConfig:
    """Serializes a config from json."""
    uuid = json_dict.get("uuid", "").strip()
    pin = json_dict.get("pin", "").strip()
    leds = json_dict.get("leds", 0)
    brightness = json_dict.get("brightness", 0)
    color_order = json_dict.get("colorOrder", "").strip()
    return NeoPixelConfig(uuid, pin, leds, brightness, color_order)
