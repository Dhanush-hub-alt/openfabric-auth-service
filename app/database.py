
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Union

from app.config import DATABASE_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS user_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL
        CHECK (action IN ('read', 'write', 'delete')),
    resource TEXT NOT NULL,
    effect TEXT NOT NULL
        CHECK (effect IN ('allow', 'deny'))
);

CREATE INDEX IF NOT EXISTS idx_permissions_user_action
ON user_permissions(user_id, action);

CREATE INDEX IF NOT EXISTS idx_permissions_user_resource
ON user_permissions(user_id, resource);
"""


def get_connection(
    database_path: Optional[Union[str, Path]] = None,
) -> sqlite3.Connection:
    path = Path(database_path or DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(path), timeout=5.0)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database(
    database_path: Optional[Union[str, Path]] = None,
) -> None:
    connection = get_connection(database_path)

    try:
        connection.executescript(SCHEMA)
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


@contextmanager
def database_connection(
    database_path: Optional[Union[str, Path]] = None,
) -> Iterator[sqlite3.Connection]:
    connection = get_connection(database_path)

    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()