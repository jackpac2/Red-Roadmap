from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import MySQLConnection


class DatabaseConfigError(Exception):
    pass


def _load_env() -> None:
    root = Path(__file__).resolve().parents[1]
    user_data = os.getenv("RED_ROADMAP_USER_DATA", "")
    resources_path = os.getenv("RED_ROADMAP_RESOURCES_PATH", "")
    candidates = [
        Path(user_data) / ".env" if user_data else None,
        Path(resources_path) / ".env" if resources_path else None,
        root / "backend" / ".env",
        root / "red_roadmap" / ".env",
        root / ".env",
    ]
    for path in candidates:
        if path is not None and path.exists():
            load_dotenv(path)
            return
    load_dotenv()


class Database:
    def __init__(self) -> None:
        _load_env()
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.user = os.getenv("DB_USER", "")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "")

        if not self.user or not self.database:
            raise DatabaseConfigError("Missing DB_USER or DB_NAME in .env configuration.")

    @contextmanager
    def connect(self) -> Iterator[MySQLConnection]:
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
        except Exception:
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
