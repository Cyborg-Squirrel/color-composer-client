# Color Composer Client

## Overview

This project provides a client for the [Color Composer](https://github.com/Cyborg-Squirrel/color-composer) server to control NeoPixel LED strips.

The Color Composer Client is intended for use on the Raspberry Pi 3, 4, Zero and Zero 2 W.

## Components

*   `neopixel_config_repository.py`:  Handles database interactions for NeoPixel configurations.
*   `neopixel_renderer.py`: Interfaces with the `neopixel` library.  Handles pin initialization, brightness adjustment, and frame rendering.
*   `neopixel_thread.py`: A background worker thread that processes configuration changes and incoming RGB frame data for rendering.

## Dependencies

*   `neopixel`:  For controlling the NeoPixel LED strips.
*   `flask`: Confuguration API hosting.
*   `websockets`: Used for hosting a WebSocket to accept incoming RGB data.

## Getting Started

1.  **Install Dependencies:**

    ```bash
    pip install neopixel flask websockets adafruit-circuitpython-neopixel
    ```

    If you encounter issues, you may also need:

    ```bash
    sudo apt-get install python3-dev
    pip install RPi.GPIO
    pip install rpi_ws281x
    ```

2.  **Run the webserver:**

    ```python flask_server.py```

## Configuration

For the Raspberry Pi, Neopixel strips must have the data wire connected to GPIO10, GPIO12, GPIO18 or GPIO21.

Sound must be disabled to use GPIO18. This can be done in /boot/firmware/config.txt by changing `dtparam=audio=on` to `dtparam=audio=off` and rebooting.

### Sudo-less operation of Neopixels
Use raspi-config or modify /boot/firmware/config.txt and add the following:
`dtparam=spi=on`
`enable_uart=1`

### Pi Configuration

Each Raspberry Pi client has a configuration which contains:
* The pin or pins WS2812 LEDs are connected to
* How many WS2812 LEDs are connected to the pin
* The brightness value set for each of the WS2812 LEDs
* The RGB type for each of the WS2812 LEDs (RGB, GRB, RGBW)
* The shape for each of the WS2812 LEDs (strip, matrix, circle)
* A unique id for each of the WS2812 LEDs

The server configuration contains:
* The tcp/ip port the server should use
* The ip address of each Raspberry Pi client
* Any configured WS2812 LED groups

## Miscellaneous Notes

Each LED (R, G, B) can draw 20mA at max brightness, so one RGB module can draw up to 60mA. Keep this in mind when powering the LED strips.

If the user connects the NeoPixel strip power directly to a Raspberry Pi 5V GPIO pin, the available current is equal to the USB power supply connected to the Raspberry Pi's USB connector minus the current used to power the board. GPIO 5V pin current should be assumed to be less than 1A.

Running multiple NeoPixel strips on one Raspberry Pi at the same time appears to be unstable after sending them color data for a few minutes. [Adafruit's guide](https://learn.adafruit.com/neopixels-on-raspberry-pi/raspberry-pi-wiring) says you can only use one at a time. However, this instability only seems to appear if both NeoPixel strips are being sent new color data at the same time — one strip set to a certain color and left unchanged while another changes appears to be stable. After some testing, the timing threshold is likely greater than 30ms between strips being told to change colors.

## Pi APIs

#### /configuration

GET endpoint for retrieving the current configuration.

GET response body

| Key        | Type                  | Constraints                               | Optional |
| ---------- | --------------------- | ----------------------------------------- | -------- |
| configList | List\<NeopixelConfig> | List of LED configurations for the client | False    |

#### /configure

POST and DELETE endpoint for creating or deleting a configuration.

POST request body

| Key    | Type           | Constraints                    | Optional |
| ------ | -------------- | ------------------------------ | -------- |
| (None) | NeopixelConfig | Must be a valid NeopixelConfig | False    |

DELETE request url parameters

| Key     | Type   | Constraints              | Optional |
| ------- | ------ | ------------------------ | -------- |
| lightId | String | Must be a valid light id | False    |

NeopixelConfig object — GET requests populate all optional fields except `id` if not yet set.

| Key        | Type          | Constraints                                                                  | Optional |
| ---------- | ------------- | ---------------------------------------------------------------------------- | -------- |
| id         | String        | Unique id for the LED strip                                                  | True     |
| pin        | String        | Must be a valid pin                                                          | True     |
| brightness | Int           | 0-100                                                                        | True     |
| colorType  | enum (String) | RGB, GRB, RGBW                                                               | True     |
| shape      | enum (String) | strip, circle, matrix                                                        | True     |
| size       | String or Int | Either int (e.g. 60 lights long) or String (e.g. "20x40" for matrix lights) | True     |

#### /brightness

Sets the brightness of an LED strip.

POST request body

| Key        | Type   | Constraints                                                | Optional |
| ---------- | ------ | ---------------------------------------------------------- | -------- |
| id         | String | The id of the LED strip                                    | False    |
| brightness | Int    | Integer value from 0-100. 0 is off, 100 is max brightness. | False    |

#### Discovery

The Raspberry Pi client listens to a WebSocket configured to receive multicast messages. The client responds to the message, allowing the sender to determine its IP address.

## Design

The programmable LEDs are controlled using a system of components: the client Raspberry Pi connected to WS2812 LEDs, the server which routes requests to the appropriate client, and the app or website where the user accesses the system. This simplifies user access by connecting to one server instead of N Raspberry Pis, and enables the server to create LED groups where strips connected to different Raspberry Pi clients can be chained together and appear as one strip.

The Raspberry Pi clients can light the WS2812 LEDs with pre-programmed light effects or with a stream of individual per-pixel color values. Pre-programmed light effects are provided a color palette and a conditional check which tells the client when to stop showing the effect.

Color palettes can be one of the following:
* One solid color
* A gradient of 2 or more colors
* Solid colors for a specified percentage of the WS2812 LEDs — example: red for the first 33%, white for the middle 33%, and blue for the last 33%

Conditional checks can be one of the following:
* Until the effect is disabled
* For a specified amount of time
* Until the effect has done N iterations

Streamed color data includes:
* 24-bit RGB color data for every pixel in the WS2812 LEDs
* An optional timestamp for when it should be displayed; no timestamp means show immediately

### Render Pipeline

1. Get effect step for each effect for the strip — returns a list of RGB values equal to the number of NeoPixels
2. Apply layers — modes: average (average RGB values of layers), priority (top layer always shown if it has active pixels), layer (algorithm below)
3. Segment out to NeoPixel strips — create one layer buffer per effect, segment buffers to different NeoPixel strips if it is a NeoPixel group, reverse buffer for LEDs where configured
4. Send color data to Pi clients to be displayed

### Layering Algorithm

Weighted average of light effects. Lower number effects are higher priority.

* One effect — no averaging needed
* Two effects — effect 0 gets 66% weight, effect 1 gets 33%
* More than two effects — effect 0 gets 50% weight, each subsequent effect gets half the weight of the next highest priority (25%, 12.5%, 6.25%...). Effects with weight below 1% are removed from the average.

### Power Limits

The power supply connected to a NeoPixel light strip may not accommodate it at full brightness on all R, G, and B LEDs. Brightness limits should be configurable by the user depending on the power supply to protect against unintended current overdraw.

## Platform IO and Flashing

### Reverse TFT Feather

Enter bootloader mode:
1. Press and hold the BOOT/DFU button. Don't let go yet.
2. Press and release the Reset button while still holding BOOT/DFU.
3. Release the BOOT/DFU button.

BOOT/DFU and Reset buttons are both labelled "reset" — try the combination above with both.

### NightDriver / PlatformIO

List serial devices:
```bash
ls /dev/tty.*
ls /dev/cu.*
```

Upload firmware:
```bash
pio run -e (environment) --target upload
# example:
pio run -e ledstrip_feather --target upload
```

## Resources

*   [Adafruit NeoPixels on Raspberry Pi guide](https://learn.adafruit.com/neopixels-on-raspberry-pi/overview)

## Contributing

*   Create a pull request
*   Explain your changes
*   The GitHub workflow must pass
