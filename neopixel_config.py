"""
The NeoPixel config object.
"""

import json

from validation_result import ValidationResult


class NeoPixelConfig:
    # The server assigned uuid of these LEDs
    uuid: str

    # The data pin connected to the LEDs
    pin: str

    # The number of LEDs
    leds: int

    # Int value from 0 to 100 representing the brightness of these LEDs
    brightness: int

    def __init__(self, uuid: str, pin: str, leds: int, brightness: int):
        self.uuid = uuid
        self.pin = pin
        self.leds = leds
        self.brightness = brightness

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
                "LED strip " + self.uuid + " must be assined to pin D10, D12, D18 or D21",
            )
        return ValidationResult(True, "")

    def to_json(self) -> str:
        """Serializes this config to json."""
        return json.dumps(
            {
                "id": self.uuid,
                "pin": self.pin,
                "leds": self.leds,
                "brightness": self.brightness,
            }
        )


def from_json(json_dict: dict) -> NeoPixelConfig:
    """Serializes a config from json."""
    id = json_dict.get("id", "").strip()
    pin = json_dict.get("pin", "").strip()
    leds = json_dict.get("leds", 0)
    brightness = json_dict.get("brightness", 0)
    return NeoPixelConfig(id, pin, leds, brightness)
