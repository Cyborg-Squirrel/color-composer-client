from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="color-composer-client",
    version="0.1.0",
    author="Ashley",
    description="A client for Color Composer server to control NeoPixel LED strips",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Cyborg-Squirrel/color-composer-client",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "websockets>=10.0",
        "adafruit-circuitpython-neopixel>=6.0.0",
        "adafruit-blinka>=7.0.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
    entry_points={
        "console_scripts": [
            "color-composer-client=color_composer_client.flask_server:main",
        ],
    },
)
