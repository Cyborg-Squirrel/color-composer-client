"""
The NeoPixel config object.
"""

import json

from validation_result import ValidationResult


class NeoPixelConfig:
    # The server assigned id of these LEDs
    id: str

    # The data pin connected to the LEDs
    pin: str

    # The number of LEDs
    leds: int

    # Int value from 0 to 100 representing the brightness of these LEDs
    brightness: int

    def __init__(self, id: str, pin: str, leds: int, brightness: int):
        self.id = id
        self.pin = pin
        self.leds = leds
        self.brightness = brightness

    def check_validity(self) -> ValidationResult:
        if self.id.isspace() or len(self.id) == 0:
            return ValidationResult(False, "LED strip id must be non-blank")
        if self.leds < 1:
            return ValidationResult(
                False, "LED strip " + self.id + " must have more than 0 LEDs."
            )
        if self.brightness < 0 or self.brightness > 100:
            return ValidationResult(
                False,
                "LED strip "
                + self.id
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
                "LED strip " + self.id + " must be assined to pin D10, D12, D18 or D21",
            )
        return ValidationResult(True, "")

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "pin": self.pin,
                "leds": self.leds,
                "brightness": self.brightness,
            }
        )


def from_json(json_dict: dict) -> NeoPixelConfig:
    id = json_dict.get("id", "").strip()
    pin = json_dict.get("pin", "").strip()
    leds = json_dict.get("leds", 0)
    brightness = json_dict.get("brightness", 0)
    return NeoPixelConfig(id, pin, leds, brightness)
