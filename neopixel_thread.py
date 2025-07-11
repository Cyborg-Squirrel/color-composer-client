"""
The NeoPixel thread. Receives configs and color data on the multiprocessing
queue for the neopixel_renderer.
"""

import logging
import multiprocessing as mp
from queue import Empty

import neopixel_config as npc
from neopixel_renderer import NeoPixelRenderer
from rgb_frame import RgbFrame

_logger: logging.Logger
_renderer: NeoPixelRenderer

def neopixel_thread(queue: mp.Queue, logger: logging.Logger):
    """Starts the thread. This will run in the background until the process is killed."""
    _logger = logger
    _logger.info("Starting neopixel thread...")
    # One hundredth of a second
    queue_timeout_fast = 1 / 100
    # One second
    queue_timeout_slow = 1
    idle = False
    _renderer = NeoPixelRenderer(_logger)
    while True:
        try:
            queue_msg = queue.get(
                timeout=queue_timeout_fast if not idle else queue_timeout_slow
            )
        except Empty:
            queue_msg = None
        if queue_msg is not None and queue_msg.isinstance(npc.NeoPixelConfig):
            _logger.debug("Received NeoPixelConfig %s", queue_msg.to_json())
            _update_config(queue_msg)
        elif queue_msg is not None and queue_msg.isinstance(list):
            _logger.debug("Received NeoPixelConfig list")
            for cfg in queue_msg:
                _logger.debug("Config %s", queue_msg.to_json())
                _update_config(cfg)
        elif queue_msg is not None and queue_msg.isinstance(RgbFrame):
            _handle_new_frame(queue_msg)
        idle = _renderer.queue_empty() and queue_msg is None
        if not _renderer.queue_empty():
            _renderer.render_queue()

def _update_config(new_config: npc.NeoPixelConfig):
    validation_result = new_config.check_validity()
    if validation_result.valid:
        _renderer.update_config(new_config)
    else:
        _logger.error("Invalid NeoPixelConfig! %s", validation_result.reason)


def _handle_new_frame(frame: RgbFrame):
    if frame.options.clear_buffer:
        _renderer.clear_buffer(frame.light_id)

    # If the timestamp is set to 0, render now.
    # Otherwise queue it to be rendered in the future.
    if frame.timestamp == 0:
         _renderer.render_frame(frame)
    else:
        _renderer.queue_frame(frame)