"""Tests for GlobalSettingsRepository class."""

import os
import sqlite3
import tempfile
from unittest.mock import Mock

import pytest

from color_composer_client.global_settings import GlobalSettings
from color_composer_client.global_settings_repository import \
    GlobalSettingsRepository


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
    """Fixture providing a GlobalSettingsRepository instance."""
    repo = GlobalSettingsRepository(temp_db, mock_logger)
    repo.init()
    return repo


class TestGlobalSettingsRepositoryInitialization:
    """Tests for GlobalSettingsRepository initialization and table creation."""

    def test_repository_initialization(self, temp_db, mock_logger):
        """Test creating a repository instance."""
        repo = GlobalSettingsRepository(temp_db, mock_logger)
        assert repo.database_name == temp_db
        assert repo.logger == mock_logger

    def test_init_creates_table(self, temp_db, mock_logger):
        """Test that init() method creates the database table."""
        repo = GlobalSettingsRepository(temp_db, mock_logger)
        result = repo.init()
        
        # Verify the table was created
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='global_settings'"
            )
            result_row = cursor.fetchone()
            assert result_row is not None

    def test_init_creates_table_successfully(self, temp_db, mock_logger):
        """Test that init() creates the table successfully."""
        repo = GlobalSettingsRepository(temp_db, mock_logger)
        repo.init()
        
        # Verify the table was created
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='global_settings'"
            )
            result = cursor.fetchone()
            assert result is not None

    def test_init_idempotent(self, repository):
        """Test that init() can be called multiple times safely."""
        # Call init() again, should not raise any errors
        repository.init()
        
        # Verify the table still exists
        with sqlite3.connect(repository.database_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='global_settings'"
            )
            result = cursor.fetchone()
            assert result is not None


class TestGlobalSettingsRepositorySave:
    """Tests for saving settings to the database."""

    def test_save_settings(self, repository):
        """Test saving settings."""
        settings = GlobalSettings(power_limit=100)
        repository.create(settings)
        
        retrieved = repository.get_settings()
        assert retrieved is not None
        assert retrieved.power_limit == 100

    def test_save_settings_with_zero_power_limit(self, repository):
        """Test saving settings with zero power limit."""
        settings = GlobalSettings(power_limit=0)
        repository.create(settings)
        
        retrieved = repository.get_settings()
        assert retrieved.power_limit == 0

    def test_save_settings_with_large_power_limit(self, repository):
        """Test saving settings with large power limit."""
        settings = GlobalSettings(power_limit=5000)
        repository.create(settings)
        
        retrieved = repository.get_settings()
        assert retrieved.power_limit == 5000

    def test_save_preserves_all_fields(self, repository):
        """Test that all settings fields are preserved when saving."""
        settings = GlobalSettings(power_limit=250)
        repository.create(settings)
        
        retrieved = repository.get_settings()
        assert retrieved.power_limit == settings.power_limit


class TestGlobalSettingsRepositoryRead:
    """Tests for reading settings from the database."""

    def test_read_returns_none_when_empty(self, repository):
        """Test that read() returns None when no settings exist."""
        result = repository.get_settings()
        assert result is None

    def test_read_existing_settings(self, repository):
        """Test reading existing settings."""
        settings = GlobalSettings(power_limit=150)
        repository.create(settings)
        
        retrieved = repository.get_settings()
        assert retrieved is not None
        assert isinstance(retrieved, GlobalSettings)
        assert retrieved.power_limit == 150

    def test_read_returns_correct_type(self, repository):
        """Test that read() returns GlobalSettings object."""
        settings = GlobalSettings(power_limit=75)
        repository.create(settings)
        
        retrieved = repository.get_settings()
        assert isinstance(retrieved, GlobalSettings)


class TestGlobalSettingsRepositoryUpdate:
    """Tests for updating settings in the database."""

    def test_update_settings(self, repository):
        """Test updating existing settings."""
        original = GlobalSettings(power_limit=100)
        repository.create(original)
        
        updated = GlobalSettings(power_limit=200)
        repository.update(updated)
        
        retrieved = repository.get_settings()
        assert retrieved.power_limit == 200

    def test_update_to_zero(self, repository):
        """Test updating settings to zero power limit."""
        original = GlobalSettings(power_limit=100)
        repository.create(original)
        
        updated = GlobalSettings(power_limit=0)
        repository.update(updated)
        
        retrieved = repository.get_settings()
        assert retrieved.power_limit == 0

    def test_update_to_large_value(self, repository):
        """Test updating settings to large power limit."""
        original = GlobalSettings(power_limit=100)
        repository.create(original)
        
        updated = GlobalSettings(power_limit=9999)
        repository.update(updated)
        
        retrieved = repository.get_settings()
        assert retrieved.power_limit == 9999

    def test_update_multiple_times(self, repository):
        """Test updating settings multiple times."""
        repository.create(GlobalSettings(power_limit=100))
        repository.update(GlobalSettings(power_limit=200))
        repository.update(GlobalSettings(power_limit=300))
        
        retrieved = repository.get_settings()
        assert retrieved.power_limit == 300

class TestGlobalSettingsRepositoryErrorHandling:
    """Tests for error handling in the repository."""

    def test_logger_called_on_error(self, temp_db, mock_logger):
        """Test that logger is called when database error occurs."""
        repo = GlobalSettingsRepository("/invalid/path/db.db", mock_logger)
        repo.init()
        
        # Attempt operation that will fail
        settings = GlobalSettings(power_limit=100)
        repo.create(settings)
        
        # Logger should have been called
        assert mock_logger.error.called

    def test_read_handles_database_errors(self, temp_db, mock_logger):
        """Test that read handles database errors gracefully."""
        repo = GlobalSettingsRepository("/invalid/path/db.db", mock_logger)
        result = repo.get_settings()
        assert result is None

    def test_operations_complete_despite_invalid_db(self, mock_logger):
        """Test that operations complete without raising exceptions on invalid db."""
        repo = GlobalSettingsRepository("/invalid/path/db.db", mock_logger)
        settings = GlobalSettings(power_limit=100)
        
        # None of these should raise exceptions
        repo.init()
        repo.create(settings)
        repo.get_settings()
        repo.update(settings)
