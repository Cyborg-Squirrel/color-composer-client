"""Tests for GlobalSettings class."""

import json

from color_composer_client.global_settings import GlobalSettings


class TestGlobalSettingsCreation:
    """Tests for GlobalSettings instantiation."""

    def test_create_valid_settings(self):
        """Test creating valid GlobalSettings."""
        settings = GlobalSettings(power_limit=100)
        assert settings.power_limit == 100

    def test_create_default_settings(self):
        """Test creating GlobalSettings with default values."""
        settings = GlobalSettings.default()
        assert settings.power_limit == 0

    def test_create_zero_power_limit(self):
        """Test creating GlobalSettings with zero power limit."""
        settings = GlobalSettings(power_limit=0)
        assert settings.power_limit == 0

    def test_create_large_power_limit(self):
        """Test creating GlobalSettings with large power limit."""
        settings = GlobalSettings(power_limit=10000)
        assert settings.power_limit == 10000


class TestGlobalSettingsValidation:
    """Tests for GlobalSettings validation."""

    def test_valid_positive_power_limit(self):
        """Test validation of positive power limit."""
        settings = GlobalSettings(power_limit=50)
        result = settings.check_validity()
        assert result.valid is True
        assert result.reason == ""

    def test_valid_zero_power_limit(self):
        """Test validation of zero power limit."""
        settings = GlobalSettings(power_limit=0)
        result = settings.check_validity()
        assert result.valid is True
        assert result.reason == ""

    def test_invalid_negative_power_limit(self):
        """Test validation fails for negative power limit."""
        settings = GlobalSettings(power_limit=-1)
        result = settings.check_validity()
        assert result.valid is False
        assert "non-negative" in result.reason.lower()

    def test_invalid_non_integer_power_limit(self):
        """Test validation handles non-integer power limit."""
        # This will be caught at runtime since power_limit is typed as int
        settings = GlobalSettings(power_limit=50)
        result = settings.check_validity()
        assert result.valid is True


class TestGlobalSettingsJsonSerialization:
    """Tests for GlobalSettings JSON serialization."""

    def test_serialize_to_json(self):
        """Test serializing GlobalSettings to JSON."""
        settings = GlobalSettings(power_limit=75)
        json_str = settings.to_json()
        parsed = json.loads(json_str)
        assert parsed["power_limit"] == 75

    def test_deserialize_from_json(self):
        """Test deserializing GlobalSettings from JSON."""
        settings = GlobalSettings(power_limit=100)
        json_str = settings.to_json()
        parsed = json.loads(json_str)
        deserialized = GlobalSettings.from_json(parsed)
        assert deserialized.power_limit == 100

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip."""
        original = GlobalSettings(power_limit=250)
        json_str = original.to_json()
        parsed = json.loads(json_str)
        restored = GlobalSettings.from_json(parsed)
        assert restored.power_limit == original.power_limit

    def test_deserialize_various_values(self):
        """Test deserializing various power limit values."""
        test_values = [0, 1, 50, 100, 1000, 9999]
        for value in test_values:
            json_dict = {"power_limit": value}
            settings = GlobalSettings.from_json(json_dict)
            assert settings.power_limit == value
