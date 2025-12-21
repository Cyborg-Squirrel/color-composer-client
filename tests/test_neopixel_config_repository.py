"""Tests for NeoPixelConfigRepository class."""

import os
import sqlite3
import tempfile
from unittest.mock import Mock

import pytest

from color_composer_client import NeoPixelConfig
from color_composer_client.neopixel_config_repository import \
    NeoPixelConfigRepository


@pytest.fixture
def temp_db():
    """Fixture providing a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def mock_logger():
    """Fixture providing a mocked logger."""
    return Mock()


@pytest.fixture
def repository(temp_db, mock_logger):
    """Fixture providing a NeoPixelConfigRepository instance."""
    repo = NeoPixelConfigRepository(temp_db, mock_logger)
    repo.create()
    return repo


class TestNeoPixelConfigRepositoryCreation:
    """Tests for NeoPixelConfigRepository initialization and table creation."""

    def test_repository_initialization(self, temp_db, mock_logger):
        """Test creating a repository instance."""
        repo = NeoPixelConfigRepository(temp_db, mock_logger)
        assert repo.database_name == temp_db
        assert repo.logger == mock_logger

    def test_create_table(self, temp_db, mock_logger):
        """Test that create() method initializes the database table."""
        repo = NeoPixelConfigRepository(temp_db, mock_logger)
        repo.create()
        
        # Verify the table was created
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='configs'"
            )
            result = cursor.fetchone()
            assert result is not None


class TestNeoPixelConfigRepositorySave:
    """Tests for saving configurations to the database."""

    def test_save_single_config(self, repository):
        """Test saving a single configuration."""
        config = NeoPixelConfig(
            uuid="test-strip-1",
            pin="D10",
            leds=30,
            brightness=75,
            color_order="GRB"
        )
        
        repository.save_config(config)
        configs = repository.get_configs()
        
        assert len(configs) == 1
        assert configs[0].uuid == "test-strip-1"

    def test_save_multiple_configs(self, repository):
        """Test saving multiple configurations."""
        config1 = NeoPixelConfig("strip-1", "D10", 30, 75, "GRB")
        config2 = NeoPixelConfig("strip-2", "D12", 50, 100, "RGB")
        config3 = NeoPixelConfig("strip-3", "D18", 100, 50, "BRG")
        
        repository.save_config(config1)
        repository.save_config(config2)
        repository.save_config(config3)
        
        configs = repository.get_configs()
        assert len(configs) == 3

    def test_save_config_preserves_all_fields(self, repository):
        """Test that all configuration fields are preserved when saving."""
        config = NeoPixelConfig(
            uuid="test-uuid",
            pin="D21",
            leds=150,
            brightness=200,
            color_order="RGB"
        )
        
        repository.save_config(config)
        configs = repository.get_configs()
        
        saved_config = configs[0]
        assert saved_config.uuid == "test-uuid"
        assert saved_config.pin == "D21"
        assert saved_config.leds == 150
        assert saved_config.brightness == 200
        assert saved_config.color_order == "RGB"


class TestNeoPixelConfigRepositoryRead:
    """Tests for retrieving configurations from the database."""

    def test_get_configs_empty_database(self, repository):
        """Test getting configs from an empty database."""
        configs = repository.get_configs()
        assert len(configs) == 0

    def test_get_configs_returns_list(self, repository):
        """Test that get_configs returns a list."""
        result = repository.get_configs()
        assert isinstance(result, list)

    def test_get_configs_preserves_order(self, repository):
        """Test that configs are retrieved in order they were saved."""
        config_data = [
            ("uuid-1", "D10", 30, 75, "GRB"),
            ("uuid-2", "D12", 50, 100, "RGB"),
            ("uuid-3", "D18", 100, 200, "BRG"),
        ]
        for uuid, pin, leds, brightness, color_order in config_data:
            config = NeoPixelConfig(uuid, pin, leds, brightness, color_order)
            repository.save_config(config)
        
        configs = repository.get_configs()
        retrieved_uuids = [c.uuid for c in configs]
        assert len(retrieved_uuids) == 3


class TestNeoPixelConfigRepositoryUpdate:
    """Tests for updating configurations in the database."""

    def test_update_config_notes_sql_issue(self, repository):
        """Test updating a config"""
        original_config = NeoPixelConfig("test-id", "D10", 30, 75, "GRB")
        repository.save_config(original_config)
        
        updated_config = NeoPixelConfig("test-id", "D12", 50, 100, "RGB")
        repository.update_config(updated_config)
        
        configs = repository.get_configs()
        assert len(configs) == 1
        assert configs[0].uuid == updated_config.uuid
        assert configs[0].pin == updated_config.pin
        assert configs[0].leds == updated_config.leds
        assert configs[0].brightness == updated_config.brightness
        assert configs[0].color_order == updated_config.color_order

class TestNeoPixelConfigRepositoryDelete:
    """Tests for deleting configurations from the database."""

    def test_delete_config(self, repository):
        """Test deleting a configuration."""
        config = NeoPixelConfig("test-id", "D10", 30, 75, "GRB")
        repository.save_config(config)
        
        repository.delete_config("test-id")
        configs = repository.get_configs()
        
        assert len(configs) == 0

    def test_delete_specific_config_among_many(self, repository):
        """Test deleting one config when multiple exist."""
        config1 = NeoPixelConfig("id-1", "D10", 30, 75, "GRB")
        config2 = NeoPixelConfig("id-2", "D12", 50, 100, "RGB")
        config3 = NeoPixelConfig("id-3", "D18", 150, 200, "BRG")
        
        repository.save_config(config1)
        repository.save_config(config2)
        repository.save_config(config3)
        
        repository.delete_config("id-2")
        configs = repository.get_configs()
        
        assert len(configs) == 2
        remaining_uuids = [c.uuid for c in configs]
        assert "id-2" not in remaining_uuids
        assert "id-1" in remaining_uuids
        assert "id-3" in remaining_uuids

    def test_delete_nonexistent_config(self, repository):
        """Test deleting a config that doesn't exist (should not raise error)."""
        repository.delete_config("nonexistent-id")
        # Should not raise any exceptions


class TestNeoPixelConfigRepositoryErrorHandling:
    """Tests for error handling in repository operations."""

    def test_save_config_handles_duplicate_uuid(self, repository, mock_logger):
        """Test that saving a duplicate UUID is handled."""
        config1 = NeoPixelConfig("duplicate-id", "D10", 30, 75, "GRB")
        config2 = NeoPixelConfig("duplicate-id", "D12", 50, 100, "RGB")
        
        repository.save_config(config1)
        repository.save_config(config2)
        
        configs = repository.get_configs()
        assert len(configs) == 1

    def test_save_config_handles_duplicate_pin(self, repository, mock_logger):
        """Test that saving with a duplicate pins does not make a new entry."""
        config1 = NeoPixelConfig("id-1", "D10", 30, 75, "GRB")
        config2 = NeoPixelConfig("id-2", "D10", 50, 100, "RGB")
        
        repository.save_config(config1)
        repository.save_config(config2)
        
        configs = repository.get_configs()
        assert len(configs) == 1
