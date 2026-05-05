"""Color Composer Client - A client for Color Composer server to control NeoPixel LED strips."""

from color_composer_client.neopixel_config import NeoPixelConfig
from color_composer_client.rgb_frame import RgbFrame, RgbFrameOptions
from color_composer_client.validation_result import ValidationResult

try:
    import subprocess as _subprocess
    __version__ = "0.1." + _subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], stderr=_subprocess.DEVNULL
    ).decode().strip()
except Exception:
    __version__ = "0.1.0"

__all__ = [
    "NeoPixelConfig",
    "RgbFrame",
    "RgbFrameOptions",
    "ValidationResult",
]
