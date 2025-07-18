"""
The renderer class. Sends specified color data to the LED strip using the neopixel package.
"""

from datetime import datetime
from logging import Logger

import board
from neopixel import NeoPixel

from neopixel_config import NeoPixelConfig
from rgb_frame import RgbFrame


class NeoPixelRenderer:
    neopixels = dict[str, NeoPixel]()
    buffered_frames = list[RgbFrame]()
    logger: Logger

    def __init__(self, logger: Logger):
        self.logger = logger

    def update_config(self, config: NeoPixelConfig):
        if config.uuid in self.neopixels:
            np = self.neopixels.pop(config.pin)
            np.deinit()
        np = self.__neopixel_from_config(config)
        self.neopixels[config.uuid] = np

    def update_configs(self, config_list: list[NeoPixelConfig]):
        # deinit all neopixels to free up the GPIO pins
        for id in self.neopixels:
            self.neopixels[id].deinit()

        self.neopixels.clear()

        # Add configured NeoPixels to the dictionary
        for config in config_list:
            np = self.__neopixel_from_config(config)
            self.neopixels[config.pin] = np

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
        self.buffered_frames[:] = [
            f for f in self.buffered_frames if getattr(f, "pin", None) != pin
        ]

    def render_frame(self, frame: RgbFrame):
        for pin, np in self.neopixels:
            self.logger.info("Neopixel configured on pin %s", pin)
        np = self.neopixels[frame.pin]
        frame_length = len(frame.rgb_data)
        for i in range(np.n if np.n <= frame_length else frame_length):
            np[i] = frame.rgb_data[i]
        np.show()

    def queue_empty(self):
        return len(self.buffered_frames) == 0

    def queue_frame(self, frame: RgbFrame):
        self.buffered_frames.append(frame)
        self.buffered_frames = sorted(
            self.buffered_frames, key=lambda frame: frame.timestamp
        )

    def render_queue(self):
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
                has_frame_with_matching_light_id = False
                for ftr in frames_to_render:
                    has_frame_with_matching_light_id |= ftr.pin == frame.pin
                if has_frame_with_matching_light_id:
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

    def set_brightness(self, pin: str, brightness: int):
        np = self.neopixels[pin]
        np.brightness = brightness / 100

    def __neopixel_from_config(self, config: NeoPixelConfig):
        pin = self.__board_pin_from_string(config.pin)
        # Config value is 0-100, NeoPixel API is 0.0-1.0
        brightness = config.brightness / 100
        return NeoPixel(pin, config.leds, brightness=brightness, auto_write=False)

    def __board_pin_from_string(self, pin: str):
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
        return None
