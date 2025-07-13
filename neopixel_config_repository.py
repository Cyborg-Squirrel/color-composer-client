"""
The SQLite repository. Does CRUD operations for config objects in the database.
"""

import logging
import sqlite3

import neopixel_config as np_config

# Surpressing lint to allow catching more types of exceptions
# pylint: disable=broad-exception-caught

class NeoPixelConfigRepository:
    """SQL Lite access class"""

    database_name: str
    logger: logging.Logger

    def __init__(self, database_name: str, logger: logging.Logger):
        self.database_name = database_name
        self.logger = logger

    def create(self):
        """Creates the table if it doesn't exist"""
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                # Remove SQL ALTER commands after migrating Pi clients to new schema
                cursor.execute("""ALTER TABLE IF EXISTS NeopixelConfig
                               RENAME COLUMN lightId TO uuid""")
                cursor.execute("""ALTER TABLE IF EXISTS NeopixelConfig
                               RENAME TO configs""")
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS configs
                                (id INT PRIMARY KEY NOT NULL, 
                                uuid TEXT NOT NULL UNIQUE, 
                                leds INTEGER NOT NULL, 
                                pin INTEGER NOT NULL UNIQUE, 
                                brightness INTEGER NOT NULL)"""
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")

    def get_configs(self) -> list[np_config.NeoPixelConfig]:
        """Gets all configs from the database"""
        config_list = list[np_config.NeoPixelConfig]()
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT uuid, pin, leds, brightness FROM configs"
                )
                connection.commit()

                for result in cursor:
                    config = np_config.NeoPixelConfig(
                        result[0], result[1], result[2], result[3]
                    )
                    config_list.append(config)
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")
        return config_list

    def save_config(self, config: np_config.NeoPixelConfig):
        """Saves a new config to the database"""
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
                    """INSERT INTO configs (id, uuid, leds, pin, brightness) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (sql_id, config.uuid, config.leds, config.pin, config.brightness),
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
