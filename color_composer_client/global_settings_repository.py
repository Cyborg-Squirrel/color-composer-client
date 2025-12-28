"""
The SQLite repository. Does CRUD operations for global settings in the database.
"""

import logging
import sqlite3

from color_composer_client import global_settings

# Surpressing lint to allow catching more types of exceptions
# pylint: disable=broad-exception-caught


class GlobalSettingsRepository:
    """SQLite database repository for global application settings.
    
    Handles all CRUD (Create, Read, Update, Delete) operations for
    storing and retrieving the single global application settings entry.
    
    Attributes:
        database_name: Path to the SQLite database file.
        logger: Logger instance for recording database operations.
    """

    database_name: str
    logger: logging.Logger

    def __init__(self, database_name: str, logger: logging.Logger):
        """Initialize the global settings repository.
        
        Args:
            database_name: Path to the SQLite database file.
            logger: Logger instance for error and debug logging.
        """
        self.database_name = database_name
        self.logger = logger

    def init(self):
        """Create the settings table in the database if it doesn't exist.
        
        Logs any SQLite or general errors encountered during table creation.
        """
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS global_settings
                                (id INT PRIMARY KEY NOT NULL, 
                                power_limit INTEGER NOT NULL)"""
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")

    def get_settings(self) -> global_settings.GlobalSettings | None:
        """Retrieve the global settings from the database.
        
        Returns:
            GlobalSettings object if found, None if no settings exist or error occurs.
        """
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT power_limit FROM global_settings WHERE id = 1"
                )
                connection.commit()

                result = cursor.fetchone()
                if result:
                    return global_settings.GlobalSettings(result[0])
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")
        return None

    def create(self, settings: global_settings.GlobalSettings):
        """Save the global settings to the database.
        
        Args:
            settings: GlobalSettings object to save.
        """
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO global_settings (id, power_limit) 
                    VALUES (1, ?)""",
                    (settings.power_limit,),
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")

    def update(self, settings: global_settings.GlobalSettings):
        """Update the global settings in the database.
        
        Args:
            settings: GlobalSettings object with updated values.
            
        Note:
            Logs any SQLite or general errors if the update operation fails.
        """
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """UPDATE global_settings SET power_limit = ? 
                    WHERE id = 1""",
                    (settings.power_limit,),
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")
