"""
The SQLite repository. Does CRUD operations for config objects in the database.
"""

import logging
import sqlite3

from color_composer_client import neopixel_config as np_config

# Surpressing lint to allow catching more types of exceptions
# pylint: disable=broad-exception-caught


class NeoPixelConfigRepository:
    """SQLite database repository for NeoPixel configurations.
    
    Handles all CRUD (Create, Read, Update, Delete) operations for
    storing and retrieving NeoPixel LED strip configurations.
    
    Attributes:
        database_name: Path to the SQLite database file.
        logger: Logger instance for recording database operations.
    """

    database_name: str
    logger: logging.Logger

    def __init__(self, database_name: str, logger: logging.Logger):
        """Initialize the NeoPixel configuration repository.
        
        Args:
            database_name: Path to the SQLite database file.
            logger: Logger instance for error and debug logging.
        """
        self.database_name = database_name
        self.logger = logger

    def create(self):
        """Create the configs table in the database if it doesn't exist.
        
        Logs any SQLite or general errors encountered during table creation.
        """
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS configs
                                (id INT PRIMARY KEY NOT NULL, 
                                uuid VARCHAR(50) NOT NULL UNIQUE, 
                                leds INTEGER NOT NULL, 
                                pin INTEGER NOT NULL UNIQUE, 
                                brightness INTEGER NOT NULL,
                                color_order VARCHAR(4) NOT NULL)"""
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")

    def get_configs(self) -> list[np_config.NeoPixelConfig]:
        """Retrieve all NeoPixel configurations from the database.
        
        Returns:
            List of NeoPixelConfig objects. Empty list if no configs exist
            or if an error occurs during retrieval.
        """
        config_list = list[np_config.NeoPixelConfig]()
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT uuid, pin, leds, brightness, color_order FROM configs"
                )
                connection.commit()

                for result in cursor:
                    config = np_config.NeoPixelConfig(
                        result[0], result[1], result[2], result[3], result[4]
                    )
                    config_list.append(config)
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")
        return config_list

    def save_config(self, config: np_config.NeoPixelConfig):
        """Save a new NeoPixel configuration to the database.
        
        Args:
            config: NeoPixelConfig object to save.
            
        Note:
            Logs any SQLite or general errors if the save operation fails.
        """
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT id FROM configs ORDER BY id DESC LIMIT 1")
                connection.commit()
                sql_id = 0
                for result in cursor:
                    sql_id = result[0] + 1
                if sql_id == 0:
                    sql_id = 1
                cursor.execute(
                    """INSERT INTO configs (id, uuid, leds, pin, brightness, color_order) 
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        sql_id,
                        config.uuid,
                        config.leds,
                        config.pin,
                        config.brightness,
                        config.color_order,
                    ),
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")

    def update_config(self, config: np_config.NeoPixelConfig):
        """Update an existing NeoPixel configuration in the database.
        
        Args:
            config: NeoPixelConfig object with updated values.
            
        Note:
            Logs any SQLite or general errors if the update operation fails.
        """
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """UPDATE configs SET leds = ?, pin = ?, brightness = ?, color_order = ? 
                    WHERE uuid = ?""",
                    (
                        config.leds,
                        config.pin,
                        config.brightness,
                        config.color_order,
                        config.uuid,
                    ),
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")

    def delete_config(self, light_id: str):
        """Delets a config from the database"""
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "DELETE FROM configs WHERE uuid = ?",
                    (light_id,),
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")
