"""
The main class and webserver. Handles color data WebSocket streams, and config REST APIs.
"""

import logging
import multiprocessing as mp
import queue
import socket
import struct
import subprocess
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from flask import Flask, Response, jsonify, request
from websockets.exceptions import ConnectionClosed
from websockets.sync.server import serve

from color_composer_client import neopixel_config as np_config
from color_composer_client import neopixel_thread as np_thread
from color_composer_client.global_settings import GlobalSettings
from color_composer_client.global_settings_repository import \
    GlobalSettingsRepository
from color_composer_client.neopixel_config_repository import \
    NeoPixelConfigRepository
from color_composer_client.renderer_events import (BackpressureError,
                                                   GenericError,
                                                   RendererBufferStatus,
                                                   RendererEvent,
                                                   StaleFrameError)
from color_composer_client.rgb_frame import RgbFrame, RgbFrameOptions

API_PORT = 8000
WS_PORT = 8765
VERSION = "0.1.0"

# maxBytes of a log file is 5MB
# backupCount number of log files will be created until deleting old log files
handler = RotatingFileHandler("cc_client.log", maxBytes=5 * 1024 * 1024, backupCount=1)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"  # , datefmt="%Y-%m-%d %H:%M:%S.%f"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

np_config_repository = NeoPixelConfigRepository("config.db", logger)
settings_repository = GlobalSettingsRepository("config.db", logger)

app = Flask(__name__.split(".", maxsplit=1)[0])
input_queue = mp.Queue(maxsize=2)
status_queue = mp.Queue(maxsize=1)


def websocket_handler(websocket):
    """Handle incoming WebSocket connections for color data streaming.
    
    Receives binary color data from WebSocket clients, extracts rendering
    options, parses RGB values, and sends the frames to the rendering
    thread using the multiprocessing queue.
    
    Args:
        websocket: WebSocket connection object for receiving messages.
    """
    try:
        for message in websocket:
            if isinstance(message, bytes):
                options_byte = message[0]
                clear_buffer = (options_byte & 0x01) == 1
                options = RgbFrameOptions(clear_buffer)

                # The GPIO pin the LED strip is connected to
                pin_bytes = message[1:5]
                pin = pin_bytes.decode("ascii").strip()

                # The time when to display the RGB data on the strip
                timestamp_bytes = message[5:13]
                timestamp_int = int.from_bytes(timestamp_bytes, "little")
                i = 13
                color_data = list[tuple[int, int, int]]()
                while i < len(message):
                    cd = (message[i], message[i + 1], message[i + 2])
                    color_data.append(cd)
                    i += 3
                frame = RgbFrame(pin, timestamp_int, options, color_data)
                try:
                    input_queue.put_nowait(frame)
                except queue.Full:
                    __handle_response(websocket, BackpressureError(
                        "Renderer is overloaded with queued frames, "
                        "please wait before sending more frames."
                    ))
                    continue
                event: Optional[RendererEvent] = None
                try:
                    event = status_queue.get(timeout=1/50)
                except queue.Empty:
                    event = None
                __handle_response(websocket, event)
            else:
                logger.warning(
                    "Unknown message type %s must be bytes", str(type(message))
                )
    except ConnectionClosed as cc:
        logger.info(
            "WebSocket connection closed. Code: %s Reason: %s", str(cc.code), cc.reason
        )

def __handle_response(websocket, event: RendererEvent):
    # isinstance checks used instead of match/case for Python 3.9 compatibility
    if isinstance(event, RendererBufferStatus):
        payload = struct.pack("<BH", 0, event.frames_in_queue)
    elif isinstance(event, StaleFrameError):
        msg = f"Stale frame: {event.frame_timestamp} < {event.current_timestamp}"
        payload = struct.pack("<B", 1) + msg.encode("utf-8")
    elif isinstance(event, (GenericError, BackpressureError)):
        payload = struct.pack("<B", 2) + event.message.encode("utf-8")
    else:
        payload = struct.pack("<B", 3) + "No response from renderer".encode("utf-8")
    websocket.send(struct.pack("<I", len(payload)) + payload)


def broadcast_handler():
    """UDP broadcast handler. Used for network discovery."""
    multicast_group = "230.0.0.0"
    multicast_port = 8007

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((multicast_group, multicast_port))
    mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, addr = sock.recvfrom(1024)
        logger.debug(str(data))
        logger.debug(str(addr))
        # Respond to the broadcast
        socket_b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        discovery_dict = (
            '{"wsPort": '
            + str(WS_PORT)
            + ', "apiPort": '
            + str(API_PORT)
            + ', "name": '
            + '"'
            + str(socket.gethostname() + '"' + "}")
        )
        socket_b.sendto(discovery_dict.encode(), addr)


def ws_handler():
    """Routes incoming WebSocket packets to the handler function."""
    with serve(websocket_handler, "0.0.0.0", 8765) as websocket:
        websocket.serve_forever()


@app.route("/time", methods=["GET"])
def current_time():
    """Endpoint to get the current time"""
    now = datetime.now()
    now_as_millis = int(now.timestamp() * 1000)
    return jsonify({"millisSinceEpoch": now_as_millis})


@app.route("/strips-config", methods=["GET", "POST", "PATCH", "DELETE"])
def strips_config():
    """Endpoint to get, create, or delete NeoPixel configs"""
    if request.method == "GET":
        return __handle_strips_config_get()
    if request.method == "PATCH":
        return __handle_strips_config_patch()
    if request.method == "POST":
        return __handle_strips_config_post()
    if request.method == "DELETE":
        uuid = request.args.get("uuid")
        if uuid is not None:
            return __handle_strips_config_delete(uuid)
        return (jsonify({"error": "No uuid url parameter specified"}), 400)
    return (jsonify({"error": "Unsupported method " + request.method}), 400)

@app.route("/settings", methods=["GET", "PATCH", "POST"])
def global_settings():
    """Endpoint to get, create, or delete global settings"""
    if request.method == "GET":
        return __handle_settings_get()
    if request.method in ("PATCH", "POST"):
        return __handle_settings_patch_or_post()
    return (jsonify({"error": "Unsupported method " + request.method}), 400)

@app.route("/version", methods=["GET"])
def version():
    """Endpoint to get the version"""
    return jsonify({"version": VERSION})

def __handle_settings_get():
    settings = settings_repository.get_settings()
    if settings is None:
        return (jsonify({"error": "No settings found"}), 404)
    settings_json = settings.to_json()
    return Response(settings_json, mimetype="application/json")

def __handle_settings_patch_or_post():
    if request.is_json:
        json_dict = request.get_json()
        updated_config = GlobalSettings.from_json(json_dict)
        result = updated_config.check_validity()
        if result.valid:
            logger.info("Updating settings %s", updated_config.to_json())
            settings_repository.update(updated_config)
            input_queue.put_nowait(updated_config)
            return Response(status=200)
        return (jsonify({"error": "Error parsing config JSON " + result.reason}), 400)
    return (jsonify({"error": "Request must be JSON"}), 400)

def __handle_strips_config_get():
    config_list = np_config_repository.get_configs()
    jsonified_config_list = "["
    i = 0
    while i < len(config_list):
        jsonified_config_list += config_list[i].to_json()
        if i < len(config_list) - 1:
            jsonified_config_list += ","
        i += 1
    jsonified_config_list += "]"
    return Response(
        '{"configList": ' + jsonified_config_list + "}", mimetype="application/json"
    )

def __handle_strips_config_patch():
    if request.is_json:
        config_list = np_config_repository.get_configs()
        json_dict = request.get_json()
        updated_config = np_config.NeoPixelConfig.from_json(json_dict)
        result = updated_config.check_validity()
        if result.valid:
            for cfg in config_list:
                if cfg.uuid == updated_config.uuid:
                    np_config_repository.update_config(updated_config)
                    input_queue.put_nowait(updated_config)
                    return Response(status=201)
            return (
                jsonify({"error": "No config found with uuid " + updated_config.uuid}),
                400,
            )
        return (jsonify({"error": "Error parsing config JSON " + result.reason}), 400)
    return (jsonify({"error": "Request must be JSON"}), 400)


def __handle_strips_config_post():
    if request.is_json:
        json_dict = request.get_json()
        config = np_config.NeoPixelConfig.from_json(json_dict)
        result = config.check_validity()
        if result.valid:
            np_config_repository.save_config(config)
            input_queue.put_nowait(config)
            return Response(status=201)
        return (jsonify({"error": "Error parsing config JSON " + result.reason}), 400)
    return (jsonify({"error": "Request must be JSON"}), 400)


def __handle_strips_config_delete(uuid):
    np_config_repository.delete_config(uuid)
    # Update the queue consumers of the config change
    neopixel_config_list = np_config_repository.get_configs()
    input_queue.put_nowait(neopixel_config_list)
    return Response(status=201)

def __init_db():
    settings_repository.init()
    np_config_repository.create()
    settings = settings_repository.get_settings()
    if settings is None:
        default_settings = GlobalSettings.default()
        settings_repository.create(default_settings)

def __put_configs_in_queue():
    neopixel_config_list = np_config_repository.get_configs()
    settings = settings_repository.get_settings()

    input_queue.put_nowait(neopixel_config_list)
    if settings is not None:
        input_queue.put_nowait(settings)

def main():
    """Main function to start the threads:
    WebSocket handler thread, UDP broadcast handler thread, and NeoPixel thread."""
    __init_db()
    p1 = mp.Process(name="ws_handler", target=ws_handler)
    # p2 = mp.Process(name="broadcast_handler", target=broadcast_handler)
    p3 = mp.Process(
        name="neopixel_thread",
        target=np_thread.neopixel_thread,
        args=(input_queue, status_queue, logger),
    )
    p1.start()
    # p2.start()
    p3.start()

    __put_configs_in_queue()
    app.run(debug=False, use_reloader=False, port=8000, host="0.0.0.0")


if __name__ == "__main__":
    main()
