"""
The NeoPixel config object.
"""

import json

from validation_result import ValidationResult


class NeoPixelConfig:
    """Config class for NeoPixel LED strips"""

    # The server assigned uuid of these LEDs
    uuid: str

    # The data pin connected to the LEDs
    pin: str

    # The number of LEDs
    leds: int

    # Int value from 0 to 100 representing the brightness of these LEDs
    brightness: int

    # The color order (RGB, GRB, etc)
    color_order: str

    def __init__(
        self, uuid: str, pin: str, leds: int, brightness: int, color_order: str
    ):
        self.uuid = uuid
        self.pin = pin
        self.leds = leds
        self.brightness = brightness
        self.color_order = color_order

    def check_validity(self) -> ValidationResult:
        """Validates this config."""
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
            len(self.color_order) == 3
            or not "r" in self.color_order.lower()
            or not "g" in self.color_order.lower()
            or not "b" in self.color_order.lower()
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
