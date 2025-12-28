"""
The NeoPixel thread. Receives configs and color data on the multiprocessing
queue for the neopixel_renderer.
"""

import logging
import multiprocessing as mp
from queue import Empty

from color_composer_client import neopixel_config as npc
from color_composer_client.global_settings import GlobalSettings
from color_composer_client.neopixel_renderer import NeoPixelRenderer
from color_composer_client.rgb_frame import RgbFrame


def neopixel_thread(queue: mp.Queue, logger: logging.Logger):
    """Main thread function for processing NeoPixel render requests.
    
    Continuously monitors the multiprocessing queue for NeoPixelConfig updates
    and RgbFrames, updating the renderer accordingly. Runs until the process
    is terminated.
    
    Args:
        queue: Multiprocessing queue for receiving configuration and frame data.
        logger: Logger instance for recording thread events and errors.
    """
    logger.info("Starting neopixel thread...")
    # One hundredth of a second
    queue_timeout_fast = 1 / 100
    # One second
    queue_timeout_slow = 1
    idle = False
    renderer = NeoPixelRenderer(logger)
    while True:
        try:
            queue_msg = queue.get(
                timeout=queue_timeout_fast if not idle else queue_timeout_slow
            )
        except Empty:
            queue_msg = None
        if queue_msg is not None and isinstance(queue_msg, npc.NeoPixelConfig):
            logger.debug("Received NeoPixelConfig %s", queue_msg.to_json())
            _update_config(renderer, logger, queue_msg)
        elif queue_msg is not None and __is_config_list(queue_msg):
            logger.debug("Received NeoPixelConfig list")
            for cfg in queue_msg:
                logger.debug("Config %s", cfg.to_json())
                _update_config(renderer, logger, cfg)
        elif queue_msg is not None and isinstance(queue_msg, GlobalSettings):
            logger.debug("Received GlobalSettings %s", queue_msg.to_json())
            renderer.set_power_limit(queue_msg.power_limit)
        elif queue_msg is not None and isinstance(queue_msg, RgbFrame):
            _handle_new_frame(renderer, queue_msg)
        idle = renderer.queue_empty() and queue_msg is None
        if not renderer.queue_empty():
            renderer.render_queue()


def __is_config_list(queue_msg):
    if isinstance(queue_msg, list):
        return all(isinstance(m, (int, npc.NeoPixelConfig)) for m in queue_msg)
    return False


def _update_config(
    renderer: NeoPixelRenderer, logger: logging.Logger, new_config: npc.NeoPixelConfig
):
    validation_result = new_config.check_validity()
    if validation_result.valid:
        renderer.update_config(new_config)
    else:
        logger.error("Invalid NeoPixelConfig! %s", validation_result.reason)


def _handle_new_frame(renderer: NeoPixelRenderer, frame: RgbFrame):
    if frame.options.clear_buffer:
        renderer.clear_buffer(frame.pin)

    # If the timestamp is set to 0, render now.
    # Otherwise queue it to be rendered in the future.
    if frame.timestamp == 0:
        renderer.render_frame(frame)
    else:
        renderer.queue_frame(frame)
