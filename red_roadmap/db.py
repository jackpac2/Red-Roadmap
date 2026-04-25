import os
import sys
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error


class DatabaseConfigError(Exception):
    pass


def resource_path(relative_path):
    """
    Get absolute path to resource for both development
    and PyInstaller executable mode.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Database:
    def __init__(self) -> None:
        # Load .env correctly for both normal Python runs
        # and PyInstaller .exe runs
        env_path = resource_path(".env")
        load_dotenv(env_path)

        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.user = os.getenv("DB_USER", "")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "")

        if not self.user or not self.database:
            raise DatabaseConfigError(
                "Missing DB_USER or DB_NAME. Add them to red_roadmap/.env."
            )

    @contextmanager
    def connect(self):
        connection = None
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=False,
            )
            yield connection
            connection.commit()

        except Error:
            if connection is not None:
                connection.rollback()
            raise

        finally:
            if connection is not None and connection.is_connected():
                connection.close()

    def test_connection(self) -> None:
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()


def get_db() -> Database:
    return Database()