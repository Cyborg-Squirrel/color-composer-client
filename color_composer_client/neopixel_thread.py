"""
The NeoPixel thread. Receives configs and color data on the multiprocessing
queue for the neopixel_renderer.
"""

import logging
import multiprocessing as mp
import queue
from datetime import datetime
from queue import Empty

from color_composer_client import neopixel_config as npc
from color_composer_client.global_settings import GlobalSettings
from color_composer_client.neopixel_renderer import NeoPixelRenderer
from color_composer_client.renderer_events import RendererBufferStatus
from color_composer_client.rgb_frame import RgbFrame


def neopixel_thread(input_queue: mp.Queue, status_queue: mp.Queue, logger: logging.Logger):
    """Main thread function for processing NeoPixel render requests.

    Continuously monitors the multiprocessing queue for NeoPixelConfig updates
    and RgbFrames, updating the renderer accordingly. Runs until the process
    is terminated.

    Args:
        input_queue: Multiprocessing queue for receiving configuration and frame data.
        status_queue: Multiprocessing queue for emitting status updates.
        logger: Logger instance for recording thread events and errors.
    """
    logger.info("Starting neopixel thread...")
    # One hundredth of a second
    queue_timeout_fast = 1 / 100
    # One second
    queue_timeout_slow = 1
    idle = False
    dimming = False
    fade_timeout_millis = 1000
    last_frame_time = datetime.now()
    renderer = NeoPixelRenderer(logger)
    while True:
        try:
            queue_msg = input_queue.get(
                timeout=queue_timeout_fast if not idle else queue_timeout_slow
            )
        except Empty:
            queue_msg = None
        if queue_msg is not None:
            frame_received, fade_timeout_millis = _process_message(
                renderer, logger, status_queue, queue_msg, fade_timeout_millis
            )
            if frame_received:
                last_frame_time = datetime.now()
                dimming = False
        idle = renderer.queue_empty() and queue_msg is None and not dimming
        dimming = _tick_dimming(renderer, dimming, last_frame_time, fade_timeout_millis)

        if not renderer.queue_empty():
            renderer.render_queue()

def _tick_dimming(renderer, dimming, last_frame_time, fade_timeout_ms):
    if not dimming:
        elapsed_ms = (datetime.now() - last_frame_time).total_seconds() * 1000
        if elapsed_ms >= fade_timeout_ms and not renderer.is_blank():
            return True
    if dimming:
        if renderer.is_blank():
            return False
        renderer.dim()
    return dimming

def _process_message(renderer, logger, status_queue, queue_msg, fade_timeout_ms):
    if isinstance(queue_msg, npc.NeoPixelConfig):
        logger.debug("Received NeoPixelConfig %s", queue_msg.to_json())
        _update_config(renderer, logger, queue_msg)
    elif _is_config_list(queue_msg):
        logger.debug("Received NeoPixelConfig list")
        for cfg in queue_msg:
            logger.debug("Config %s", cfg.to_json())
            _update_config(renderer, logger, cfg)
    elif isinstance(queue_msg, GlobalSettings):
        logger.debug("Received GlobalSettings %s", queue_msg.to_json())
        renderer.set_power_limit(queue_msg.power_limit)
        if queue_msg.fade_timeout_millis is not None:
            fade_timeout_ms = queue_msg.fade_timeout_millis
    elif isinstance(queue_msg, RgbFrame):
        _handle_new_frame(renderer, queue_msg)
        _emit_status(status_queue, renderer, logger)
        return True, fade_timeout_ms
    return False, fade_timeout_ms

def _emit_status(status_queue: mp.Queue, renderer: NeoPixelRenderer, logger: logging.Logger):
    try:
        status_queue.put_nowait(RendererBufferStatus(frames_in_queue=len(renderer.buffered_frames)))
    except queue.Full:
        logger.warning("Status queue is full, skipping status update")
    except (OSError, ValueError) as e:
        logger.error("Failed to emit status update: %s: %s", type(e).__name__, e)

def _is_config_list(queue_msg):
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
