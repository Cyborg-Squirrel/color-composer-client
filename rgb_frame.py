"""
The RGB frame. Contains color data and rendering options.
"""

class RgbFrameOptions:
    clear_buffer: bool

    def __init__(self, clear_buffer: bool):
        self.clear_buffer = clear_buffer


class RgbFrame:
    light_id: str
    timestamp: int
    options: RgbFrameOptions
    rgb_data: list[tuple[int, int, int]]

    def __init__(
        self,
        light_id: str,
        timestamp: int,
        options: RgbFrameOptions,
        rgb_data: list[tuple[int, int, int]],
    ):
        self.light_id = light_id
        self.timestamp = timestamp
        self.options = options
        self.rgb_data = rgb_data
