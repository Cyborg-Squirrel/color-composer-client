"""
The main class and webserver. Handles color data WebSocket streams, and config REST APIs.
"""

import logging
import multiprocessing as mp
import socket
import struct
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask, Response, jsonify, request
from websockets.exceptions import ConnectionClosed
from websockets.sync.server import serve

import neopixel_config as np_config
import neopixel_thread as np_thread
from neopixel_config_repository import NeoPixelConfigRepository
from rgb_frame import RgbFrame, RgbFrameOptions

API_PORT = 8000
WS_PORT = 8765
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

cfg_repository = NeoPixelConfigRepository("config.db", logger)

app = Flask(__name__.split(".", maxsplit=1)[0])
queue = mp.Queue()


def websocket_handler(websocket):
    """WebSocket handler function"""
    try:
        for message in websocket:
            if isinstance(message, bytes):
                options_byte = message[0]
                clear_buffer = (options_byte & 0x01) == 1
                options = RgbFrameOptions(clear_buffer)

                # The GPIO pin the LED strip is connected to
                # pin_bytes = message[1:5]
                # pin = pin_bytes.decode("ascii").strip()

                # The time when to display the RGB data on the strip
                timestamp_bytes = message[5:13]
                timestamp_int = int.from_bytes(timestamp_bytes, "little")
                i = 13
                color_data = list[tuple[int, int, int]]()
                while i < len(message):
                    cd = (message[i], message[i + 1], message[i + 2])
                    color_data.append(cd)
                    i += 3
                # Get current path with the leading "/" removed
                light_id = "test"  # websocket.request.path[1:]
                frame = RgbFrame(light_id, timestamp_int, options, color_data)
                queue.put_nowait(frame)
                while not queue.empty():
                    time.sleep(1 / 100)
                websocket.send("ACK")
            else:
                logger.warning("Unknown message type %s must be bytes", str(type(message)))
    except ConnectionClosed as cc:
        logger.info("WebSocket connection closed. Code: %s Reason: %s", str(cc.code), cc.reason)


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


@app.route("/configuration", methods=["GET", "POST", "DELETE"])
def configuration():
    """Endpoint to get, create, or delete NeoPixel configs"""
    if request.method == "GET":
        return __handle_get()
    if request.method == "PATCH":
        return __handle_patch()
    if request.method == "POST":
        return __handle_post()
    if request.method == "DELETE":
        uuid = request.args.get("uuid")
        if uuid is not None:
            return __handle_delete(uuid)
        return (jsonify({"error": "No uuid url parameter specified"}), 400)
    return (jsonify({"error": "Unsupported method " + request.method}), 400)

def __handle_get():
    config_list = cfg_repository.get_configs()
    jsonified_config_list = "["
    i = 0
    while i < len(config_list):
        jsonified_config_list += config_list[i].to_json()
        if i < len(config_list) - 1:
            jsonified_config_list += ","
        i += 1
    jsonified_config_list += "]"
    return Response('{"configList": ' + jsonified_config_list + "}",
                    mimetype="application/json")

def __handle_patch():
    if request.is_json:
        config_list = cfg_repository.get_configs()
        json_dict = request.get_json()
        updated_config = np_config.from_json(json_dict)
        result = updated_config.check_validity()
        if result.valid:
            for cfg in config_list:
                if cfg.uuid == updated_config.uuid:
                    cfg_repository.update_config(updated_config)
                    queue.put_nowait(updated_config)
                    return Response(status=201)
            return (jsonify({"error": "No config found with uuid " + updated_config.uuid}), 400)
        else:
            return (jsonify({"error": "Error parsing config JSON " + result.reason}), 400)
    return (jsonify({"error": "Request must be JSON"}), 400)

def __handle_post():
    if request.is_json:
        json_dict = request.get_json()
        config = np_config.from_json(json_dict)
        result = config.check_validity()
        if result.valid:
            cfg_repository.save_config(config)
            queue.put_nowait(config)
            return Response(status=201)
        return (jsonify({"error": "Error parsing config JSON " + result.reason}), 400)
    return (jsonify({"error": "Request must be JSON"}), 400)

def __handle_delete(uuid):
    cfg_repository.delete_config(uuid)
    # Update the queue consumers of the config change
    config_list = cfg_repository.get_configs()
    queue.put_nowait(config_list)
    return Response(status=201)

def main():
    """Main function to start the threads:
    WebSocket handler thread, UDP broadcast handler thread, and NeoPixel thread."""
    cfg_repository.create()
    p1 = mp.Process(name="ws_handler", target=ws_handler)
    p2 = mp.Process(name="broadcast_handler", target=broadcast_handler)
    p3 = mp.Process(
        name="neopixel_thread",
        target=np_thread.neopixel_thread,
        args=(queue, logger),
    )
    p1.start()
    p2.start()
    p3.start()

    config_list = cfg_repository.get_configs()
    queue.put_nowait(config_list)
    app.run(debug=False, use_reloader=False, port=8000, host="0.0.0.0")


if __name__ == "__main__":
    main()
