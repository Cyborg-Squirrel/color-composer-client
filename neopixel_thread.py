import logging
import multiprocessing as mp
from queue import Empty

import neopixel_config as npc
from neopixel_renderer import NeoPixelRenderer
from rgb_frame import RgbFrame


def neopixel_thread(queue: mp.Queue, logger: logging.Logger):
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
        if type(queue_msg) is npc.NeoPixelConfig:
            logger.debug("Received NeoPixelConfig " + queue_msg.to_json())
            validation_result = queue_msg.check_validity()
            if validation_result.valid:
                renderer.update_config(queue_msg)
            else:
                logger.error("Invalid NeoPixelConfig! " + str(validation_result.reason))
        elif type(queue_msg) is list:
            logger.debug("Received NeoPixelConfig list")
            valid = True
            reason = ""
            i = 0
            while valid and i < len(queue_msg):
                cfg_validation_result = queue_msg[i].check_validity()
                valid &= cfg_validation_result.valid
                if not cfg_validation_result.valid:
                    reason = cfg_validation_result.reason
                i += 1
            if valid:
                renderer.update_configs(queue_msg)
            else:
                logger.error("Invalid config in NeoPixelConfig list! " + str(reason))
        elif type(queue_msg) is RgbFrame:
            if queue_msg.options.clear_buffer:
                renderer.clear_buffer(queue_msg.light_id)

            # If the timestamp is set to 0, render now. Otherwise queue it to be rendered in the future.
            if queue_msg.timestamp == 0:
                renderer.render_frame(queue_msg)
            else:
                renderer.queue_frame(queue_msg)

        idle = renderer.queue_empty() and queue_msg is None
        if not renderer.queue_empty():
            renderer.render_queue()
