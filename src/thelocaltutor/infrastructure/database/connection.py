"""SQLite connection manager with WAL mode and foreign-key support."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from thelocaltutor.core import config
from thelocaltutor.core.exceptions import DatabaseError

log = logging.getLogger(__name__)

_connection: sqlite3.Connection | None = None


def _make_connection(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = _make_connection(config.DB_PATH)
        log.info("Database opened at %s", config.DB_PATH)
    return _connection


def close_connection() -> None:
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None


@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise DatabaseError(str(exc)) from exc
