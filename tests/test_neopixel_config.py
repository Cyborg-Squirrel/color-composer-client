"""Tests for NeoPixelConfig class."""

import json

import pytest

from color_composer_client import NeoPixelConfig
from color_composer_client.validation_result import ValidationResult


class TestNeoPixelConfigCreation:
    """Tests for NeoPixelConfig instantiation."""

    def test_create_valid_config(self):
        """Test creating a valid NeoPixelConfig."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=75,
            color_order="GRB"
        )
        assert config.uuid == "strip-1"
        assert config.pin == "D10"
        assert config.leds == 30
        assert config.brightness == 75
        assert config.color_order == "GRB"

class TestNeoPixelConfigJsonSerialization:
    """Tests for NeoPixelConfig JSON serialization."""

    def test_json_serialize_config(self):
        """Test serializing a NeoPixelConfig."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=75,
            color_order="GRB"
        )

        config_as_json = config.to_json()
        config_as_dict = json.loads(config_as_json)
        deserialized_config = NeoPixelConfig.from_json(config_as_dict)
        
        assert deserialized_config.uuid == config.uuid
        assert deserialized_config.pin == config.pin
        assert deserialized_config.leds == config.leds
        assert deserialized_config.brightness == config.brightness
        assert deserialized_config.color_order == config.color_order


class TestNeoPixelConfigValidation:
    """Tests for NeoPixelConfig validation logic."""

    def test_valid_config(self):
        """Test that a valid config passes validation."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=75,
            color_order="GRB"
        )
        result = config.check_validity()
        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.reason == ""

    def test_empty_uuid_fails(self):
        """Test that empty UUID fails validation."""
        config = NeoPixelConfig(
            uuid="",
            pin="D10",
            leds=30,
            brightness=75,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is False
        assert "non-blank" in result.reason

    def test_whitespace_uuid_fails(self):
        """Test that whitespace-only UUID fails validation."""
        config = NeoPixelConfig(
            uuid="   ",
            pin="D10",
            leds=30,
            brightness=75,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is False

    def test_zero_leds_fails(self):
        """Test that zero LEDs fails validation."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=0,
            brightness=75,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is False
        assert "more than 0 LEDs" in result.reason

    def test_negative_leds_fails(self):
        """Test that negative LED count fails validation."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=-5,
            brightness=75,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is False

    def test_brightness_too_low(self):
        """Test that brightness below 0 fails validation."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=-1,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is False

    def test_brightness_too_high(self):
        """Test that brightness above 100 fails validation."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=101,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is False

    def test_brightness_boundary_min(self):
        """Test that brightness of 0 is valid."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=0,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is True

    def test_brightness_boundary_max(self):
        """Test that brightness of 100 is valid."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=100,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is True

    def test_invalid_pin(self):
        """Test that invalid GPIO pin fails validation."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D99",  # Invalid pin
            leds=30,
            brightness=75,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is False
        assert "D10, D12, D18 or D21" in result.reason

    @pytest.mark.parametrize("pin", ["D10", "D12", "D18", "D21"])
    def test_valid_pins(self, pin):
        """Test that all valid pins pass validation."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin=pin,
            leds=30,
            brightness=75,
            color_order="GRB"
        )
        result = config.check_validity()
        assert result.valid is True

    def test_invalid_color_order_too_short(self):
        """Test that color order with fewer than 3 letters fails."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=75,
            color_order="RG"
        )
        result = config.check_validity()
        assert result.valid is False

    def test_invalid_color_order_missing_channel(self):
        """Test that color order missing a required channel fails."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=75,
            color_order="RRR"
        )
        result = config.check_validity()
        assert result.valid is False

    @pytest.mark.parametrize("color_order", ["RGB", "GRB", "BGR", "BRG", "RBG", "GBR"])
    def test_valid_color_orders(self, color_order):
        """Test that all valid color orders pass validation."""
        config = NeoPixelConfig(
            uuid="strip-1",
            pin="D10",
            leds=30,
            brightness=75,
            color_order=color_order
        )
        result = config.check_validity()
        assert result.valid is True
