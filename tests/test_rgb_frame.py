"""Tests for RgbFrame and RgbFrameOptions classes."""

import pytest

from color_composer_client import RgbFrame, RgbFrameOptions


class TestRgbFrameOptions:
    """Tests for RgbFrameOptions configuration class."""

    def test_create_with_clear_buffer_true(self):
        """Test creating options with clear_buffer=True."""
        options = RgbFrameOptions(clear_buffer=True)
        assert options.clear_buffer is True

    def test_create_with_clear_buffer_false(self):
        """Test creating options with clear_buffer=False."""
        options = RgbFrameOptions(clear_buffer=False)
        assert options.clear_buffer is False


class TestRgbFrame:
    """Tests for RgbFrame data class."""

    def test_create_frame_with_valid_data(self):
        """Test creating a frame with valid RGB data."""
        options = RgbFrameOptions(clear_buffer=False)
        rgb_data = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        
        frame = RgbFrame(
            pin="D10",
            timestamp=1000000,
            options=options,
            rgb_data=rgb_data
        )
        
        assert frame.pin == "D10"
        assert frame.timestamp == 1000000
        assert frame.options == options
        assert frame.rgb_data == rgb_data
        assert len(frame.rgb_data) == 3

    def test_frame_with_empty_rgb_data(self):
        """Test creating a frame with no RGB data."""
        options = RgbFrameOptions(clear_buffer=True)
        
        frame = RgbFrame(
            pin="D12",
            timestamp=2000000,
            options=options,
            rgb_data=[]
        )
        
        assert len(frame.rgb_data) == 0

    def test_frame_with_single_led(self):
        """Test creating a frame for a single LED."""
        options = RgbFrameOptions(clear_buffer=False)
        
        frame = RgbFrame(
            pin="D18",
            timestamp=3000000,
            options=options,
            rgb_data=[(128, 64, 32)]
        )
        
        assert len(frame.rgb_data) == 1
        assert frame.rgb_data[0] == (128, 64, 32)

    def test_frame_with_many_leds(self):
        """Test creating a frame with many LEDs."""
        options = RgbFrameOptions(clear_buffer=False)
        rgb_data = [(i % 256, (i * 2) % 256, (i * 3) % 256) for i in range(100)]
        
        frame = RgbFrame(
            pin="D21",
            timestamp=4000000,
            options=options,
            rgb_data=rgb_data
        )
        
        assert len(frame.rgb_data) == 100

    def test_frame_timestamp_zero(self):
        """Test that timestamp of 0 is valid (means render immediately)."""
        options = RgbFrameOptions(clear_buffer=False)
        
        frame = RgbFrame(
            pin="D10",
            timestamp=0,  # Special case: render now
            options=options,
            rgb_data=[(255, 255, 255)]
        )
        
        assert frame.timestamp == 0

    @pytest.mark.parametrize("pin", ["D10", "D12", "D18", "D21"])
    def test_frame_with_valid_pins(self, pin):
        """Test creating frames with all valid pin identifiers."""
        options = RgbFrameOptions(clear_buffer=False)
        
        frame = RgbFrame(
            pin=pin,
            timestamp=5000000,
            options=options,
            rgb_data=[(255, 0, 0)]
        )
        
        assert frame.pin == pin
