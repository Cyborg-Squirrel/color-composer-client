"""Color Composer Client - A client for Color Composer server to control NeoPixel LED strips."""

from color_composer_client.neopixel_config import NeoPixelConfig
from color_composer_client.rgb_frame import RgbFrame, RgbFrameOptions
from color_composer_client.validation_result import ValidationResult

__version__ = "0.1.0"

__all__ = [
    "NeoPixelConfig",
    "RgbFrame",
    "RgbFrameOptions",
    "ValidationResult",
]
