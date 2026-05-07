"""
The renderer class. Sends specified color data to the LED strip using the neopixel package.
"""

# pylint: disable=import-error
from datetime import datetime
from logging import Logger

import board
import neopixel

from color_composer_client.neopixel_config import NeoPixelConfig
from color_composer_client.rgb_frame import RgbFrame


class NeoPixelRenderer:
    """Manages NeoPixel LED strip rendering and configuration.
    
    Attributes:
        neopixels: Dictionary mapping GPIO pins to NeoPixel objects.
        buffered_frames: List of RGB frames waiting to be rendered.
        logger: Logger instance for debugging and error reporting.
    """

    neopixels = dict[str, neopixel.NeoPixel]()
    configs = dict[str, NeoPixelConfig]()
    buffered_frames = list[RgbFrame]()
    logger: Logger
    power_limit: int = 0

    def __init__(self, logger: Logger):
        """Initialize the NeoPixel renderer.
        
        Args:
            logger: Logger instance for recording events and errors.
        """
        self.logger = logger

    def set_power_limit(self, power_limit: int):
        """Set the power limit for all NeoPixel strips.
        
        Args:
            power_limit: Maximum power in milliamps.
        """
        self.power_limit = power_limit

    def update_config(self, config: NeoPixelConfig):
        """Update or create a NeoPixel configuration.
        
        If a NeoPixel already exists on the specified pin, it will be
        deinitialized and replaced with the new configuration.
        
        Args:
            config: NeoPixelConfig object containing LED strip settings.
        """
        if config.pin in self.neopixels:
            np = self.neopixels.pop(config.pin)
            np.deinit()
        np = self.__neopixel_from_config(config)
        self.neopixels[config.pin] = np
        self.configs[config.pin] = config

    def update_configs(self, config_list: list[NeoPixelConfig]):
        """Update all NeoPixel configurations at once.
        
        Deinits all existing NeoPixels, clears the configuration, and
        applies a new list of configurations. Removes any buffered
        frames for configurations no longer in use.
        
        Args:
            config_list: List of NeoPixelConfig objects to apply.
        """
        # deinit all neopixels to free up the GPIO pins
        for key in self.neopixels:
            self.neopixels[key].deinit()

        self.neopixels.clear()
        self.configs.clear()

        # Add configured NeoPixels to the dictionary
        for config in config_list:
            np = self.__neopixel_from_config(config)
            self.neopixels[config.pin] = np
            self.configs[config.pin] = config

        # Remove any buffered frames for NeoPixels which have been removed from the config
        i = 0
        while i < len(self.buffered_frames):
            frame = self.buffered_frames[i]
            keep_in_buffer = False
            for pin in self.neopixels:
                keep_in_buffer |= frame.pin == pin
            if keep_in_buffer:
                i += 1
            else:
                self.buffered_frames.remove(frame)

    def clear_buffer(self, pin: str):
        """Clear all buffered frames for a specific pin.
        
        Args:
            pin: GPIO pin identifier to clear frames for.
        """
        self.buffered_frames[:] = [
            f for f in self.buffered_frames if getattr(f, "pin", None) != pin
        ]

    def render_frame(self, frame: RgbFrame):
        """Render a single RGB frame to the NeoPixel strip.
        
        Args:
            frame: RgbFrame object containing color data and pin information.
        """
        np = self.neopixels[frame.pin]
        config = self.configs[frame.pin]
        frame_length = len(frame.rgb_data)
        if self.power_limit > 0:
            estimated_power = self.__calculate_power_usage(frame)
            if estimated_power >= self.power_limit and estimated_power > 0:
                new_brightness = int(config.brightness * self.power_limit / estimated_power)
                self.set_brightness(frame.pin, new_brightness)
            else:
                self.set_brightness(frame.pin, config.brightness)
        for i in range(np.n if np.n <= frame_length else frame_length):
            np[i] = frame.rgb_data[i]
        np.show()

    def queue_empty(self):
        """Check if the render queue is empty.
        
        Returns:
            True if no frames are buffered, False otherwise.
        """
        return len(self.buffered_frames) == 0

    def queue_frame(self, frame: RgbFrame):
        """Add an RGB frame to the render queue.
        
        Frames are sorted by timestamp to ensure rendering order.
        
        Args:
            frame: RgbFrame object to queue for rendering.
        """
        self.buffered_frames.append(frame)
        self.buffered_frames = sorted(
            self.buffered_frames, key=lambda frame: frame.timestamp
        )

    def render_queue(self):
        """Process and render any frames in the queue that are ready.
        
        Renders frames with timestamps within a 10ms window of the current time.
        Removes frames that are more than 1 second old to prevent stale data.
        """
        now = datetime.now()
        now_as_millis = int(now.timestamp() * 1000)
        # Render the frame in the queue if it is within a 100th of a second
        threshold = int((1 / 100) * 1000)
        i = 0
        frames_to_render = list[RgbFrame]()

        while i < len(self.buffered_frames):
            frame = self.buffered_frames[i]
            diff = abs(frame.timestamp - now_as_millis)
            if diff <= threshold:
                has_frame_with_matching_pin = False
                for ftr in frames_to_render:
                    has_frame_with_matching_pin |= ftr.pin == frame.pin
                if has_frame_with_matching_pin:
                    i += 1
                else:
                    frames_to_render.append(frame)
                    self.buffered_frames.remove(frame)
            elif frame.timestamp < (now_as_millis - 1000):
                # Remove frames with timestamps older than 1 second ago
                # Somehow it got missed, so remove it from the buffer
                self.logger.warning(
                    "Buffered frame drop! Frame timestamp: "
                    + str(frame.timestamp)
                    + " system time one second ago: "
                    + str(now_as_millis - 1000)
                    + " pin: "
                    + str(frame.pin)
                )
                self.buffered_frames.remove(frame)
            else:
                i += 1

        for frame in frames_to_render:
            self.render_frame(frame)

    def dim(self):
        """Reduce every LED on all strips by 10 per channel, flooring at 0."""
        for np in self.neopixels.values():
            for i in range(np.n):
                r, g, b = np[i]
                np[i] = (max(0, r - 2), max(0, g - 2), max(0, b - 2))
            np.show()

    def is_blank(self) -> bool:
        """Return True if every LED on all strips is (0, 0, 0)."""
        for np in self.neopixels.values():
            for i in range(np.n):
                if np[i] != (0, 0, 0):
                    return False
        return True

    def set_brightness(self, pin: str, brightness: int):
        """Set the brightness for a specific NeoPixel strip.
        
        Args:
            pin: GPIO pin identifier for the target strip.
            brightness: Brightness value from 0 to 100.
        """
        np = self.neopixels[pin]
        np.brightness = brightness / 100

    def __calculate_power_usage(self, frame: RgbFrame) -> int:
        """Estimate the power usage of a NeoPixel strip.
        
        Args:
            frame: RgbFrame object to estimate power usage of.
            
        Returns:
            Estimated power usage in milliamps.
        """
        # Each NeoPixel can draw up to 60mA at full brightness 20mA per LED (R + G + B)
        max_power_per_led_ma = 60
        estimated_power = 0
        for rgb in frame.rgb_data:
            r, g, b = rgb
            led_power = (r / 255 + g / 255 + b / 255) * max_power_per_led_ma
            estimated_power += led_power
        return int(estimated_power)

    def __neopixel_from_config(self, config: NeoPixelConfig):
        """Create a NeoPixel object from configuration.
        
        Args:
            config: NeoPixelConfig containing strip settings.
            
        Returns:
            neopixel.NeoPixel object configured and ready to use.
        """
        pin = self.__board_pin_from_string(config.pin)
        # Config value is 0-100, NeoPixel API is 0.0-1.0
        brightness = config.brightness / 100
        return neopixel.NeoPixel(
            pin,
            config.leds,
            brightness=brightness,
            auto_write=False,
            pixel_order=config.color_order,
        )

    def __board_pin_from_string(self, pin: str):
        """Convert pin string identifier to board pin object.
        
        Args:
            pin: Pin identifier string (D10, D12, D18, or D21).
            
        Returns:
            board pin object or None if pin is invalid.
        """
        # For Raspberry Pis pin D10 is recommended as the Neopixel data pin
        # because it can be configured for use without sudo
        # Add dtparam=spi=on and enable_uart=1 to /boot/firmware/config.txt
        if pin == "D10":
            return board.D10
        if pin == "D12":
            return board.D12
        if pin == "D18":
            return board.D18
        if pin == "D21":
            return board.D21
        raise ValueError("Invalid pin identifier: " + pin)
