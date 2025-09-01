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

2.  **Run the webserver:**

    ```python flask_server.py```

## Configuration

For the Raspberry Pi, Neopixel strips must have the data wire connected to GPIO10, GPIO12, GPIO18 or GPIO21.

Sound must be disabled to use GPIO18. This can be done in /boot/firmware/config.txt by changing `dtparam=audio=on` to `dtparam=audio=off` and rebooting.

### Sudo-less operation of Neopixels
Use raspi-config or modify /boot/firmware/config.txt and add the following:
`dtparam=spi=on`
`enable_uart=1`

## Contributing

*   Create a pull request
*   Explain your changes
*   The GitHub workflow must pass
