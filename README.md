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
