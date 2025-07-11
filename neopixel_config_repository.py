"""
The SQLite repository. Does CRUD operations for config objects in the database.
"""

import logging
import sqlite3

import neopixel_config as np_config


class NeoPixelConfigRepository:

    database_name: str
    logger: logging.Logger

    def __init__(self, database_name: str, logger: logging.Logger):
        self.database_name = database_name
        self.logger = logger

    def create(self):
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                # Remove SQL ALTER commands after migrating Pi clients to new schema
                cursor.execute("""ALTER TABLE NeopixelConfig RENAME COLUMN lightId TO uuid;""")
                cursor.execute("""ALTER TABLE NeopixelConfig RENAME TO configs;""")
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS configs
                                (id INT PRIMARY KEY NOT NULL, 
                                uuid TEXT NOT NULL UNIQUE, 
                                leds INTEGER NOT NULL, 
                                pin INTEGER NOT NULL, 
                                brightness INTEGER NOT NULL)"""
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")

    def get_configs(self) -> list[np_config.NeoPixelConfig]:
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
        try:
            with sqlite3.connect(self.database_name) as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT id FROM configs ORDER BY id DESC LIMIT 1")
                connection.commit()
                id = 0
                for result in cursor:
                    id = result[0] + 1
                if id == 0:
                    id = 1
                cursor.execute(
                    """INSERT INTO configs (id, uuid, leds, pin, brightness) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (id, config.uuid, config.leds, config.pin, config.brightness),
                )
                connection.commit()
        except sqlite3.Error as e:
            self.logger.error(f"sqlite3 error {e}")
        except Exception as e:
            self.logger.error(f"Error {e}")

    def delete_config(self, light_id: str):
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
