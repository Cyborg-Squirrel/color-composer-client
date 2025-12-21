"""
The RGB frame. Contains color data and rendering options.
"""

# pylint: disable=too-few-public-methods


class RgbFrameOptions:
    """Configuration options for RGB frame rendering.
    
    Attributes:
        clear_buffer: If True, clears the frame buffer before rendering.
    """

    clear_buffer: bool

    def __init__(self, clear_buffer: bool):
        """Initialize RGB frame options.
        
        Args:
            clear_buffer: Whether to clear the buffer before rendering.
        """
        self.clear_buffer = clear_buffer


class RgbFrame:
    """Represents a single frame of RGB color data for LED rendering.
    
    Contains the color data, rendering options, and metadata needed to
    display colors on a specific LED strip.
    
    Attributes:
        pin: GPIO pin identifier for the target LED strip.
        timestamp: Unix timestamp indicating when the frame was created.
        options: RgbFrameOptions object containing rendering configuration.
        rgb_data: List of RGB tuples (R, G, B) with values 0-255 for each LED.
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
        """Initialize an RGB frame.
        
        Args:
            pin: GPIO pin identifier for the target LED strip.
            timestamp: Unix timestamp of frame creation.
            options: RgbFrameOptions object with rendering configuration.
            rgb_data: List of RGB tuples for each LED in the strip.
        """
        self.pin = pin
        self.timestamp = timestamp
        self.options = options
        self.rgb_data = rgb_data
