
import sqlite3

from app.database import initialize_database
from scripts.seed_database import seed_database


def test_database_schema_is_created(tmp_path):
    db_path = tmp_path / "test_permissions.db"

    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        result = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'user_permissions'
            """
        ).fetchone()

    assert result is not None


def test_seed_inserts_all_sample_permissions(tmp_path):
    db_path = tmp_path / "test_permissions.db"

    total = seed_database(db_path)

    assert total == 13

    with sqlite3.connect(db_path) as connection:
        denied = connection.execute(
            """
            SELECT effect
            FROM user_permissions
            WHERE user_id = ?
              AND action = ?
              AND resource = ?
            """,
            ("user123", "delete", "transactions"),
        ).fetchone()

    assert denied == ("deny",)


def test_seeding_twice_does_not_duplicate_rows(tmp_path):
    db_path = tmp_path / "test_permissions.db"

    seed_database(db_path)
    total = seed_database(db_path)

    assert total == 13