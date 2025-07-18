"""
The RGB frame. Contains color data and rendering options.
"""

# pylint: disable=too-few-public-methods

class RgbFrameOptions:
    """The options object for RGB frames."""

    clear_buffer: bool

    def __init__(self, clear_buffer: bool):
        self.clear_buffer = clear_buffer


class RgbFrame:
    """
    The RGB frame. Includes a LED strip, render options, a timestamp, 
    and the RGB values to be displayed.
    """
    pin: str
    timestamp: int
    options: RgbFrameOptions
    rgb_data: list[tuple[int, int, int]]

    def __init__(
        self,
        pin: str,
        timestamp: int,
        options: RgbFrameOptions,
        rgb_data: list[tuple[int, int, int]],
    ):
        self.pin = pin
        self.timestamp = timestamp
        self.options = options
        self.rgb_data = rgb_data
