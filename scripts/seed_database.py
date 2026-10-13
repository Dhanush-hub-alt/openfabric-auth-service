
from pathlib import Path
from typing import Optional, Union

from app.database import database_connection, initialize_database


SAMPLE_PERMISSIONS = [
    (1, "user123", "read", "transactions", "allow"),
    (2, "user123", "write", "transactions", "allow"),
    (3, "user123", "delete", "transactions", "deny"),
    (4, "user123", "read", "accounts", "allow"),
    (5, "user456", "read", "wallets/*", "allow"),
    (6, "user456", "write", "wallets/wallet-789", "allow"),
    (7, "user456", "read", "wallets/wallet-789/transactions", "allow"),
    (8, "user789", "write", "wallets/*/transactions/*", "allow"),
    (9, "admin789", "read", "*", "allow"),
    (10, "admin789", "write", "*", "allow"),
    (11, "admin789", "delete", "*", "allow"),
    (
        12,
        "iPxVX62f4EBI49taG5tXNS2r9HsS29jH@clients",
        "read",
        "accounts",
        "allow",
    ),
]


def seed_database(
    database_path: Optional[Union[str, Path]] = None,
) -> int:
    initialize_database(database_path)

    with database_connection(database_path) as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO user_permissions
                (id, user_id, action, resource, effect)
            VALUES (?, ?, ?, ?, ?)
            """,
            SAMPLE_PERMISSIONS,
        )

        connection.commit()

        total = connection.execute(
            "SELECT COUNT(*) FROM user_permissions"
        ).fetchone()[0]

    return total


if __name__ == "__main__":
    total = seed_database()
    print(f"Database ready. Permission rows: {total}")
