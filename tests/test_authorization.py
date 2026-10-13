import pytest

from app.services.authorization import get_action, check_permission


@pytest.mark.parametrize(
    "method, expected",
    [
        ("GET", "read"),
        ("POST", "write"),
        ("PUT", "write"),
        ("PATCH", "write"),
        ("DELETE", "delete"),
        ("HEAD", None),
    ],
)
def test_get_action(method, expected):
    assert get_action(method) == expected


@pytest.mark.parametrize(
    "user_id, action, resource, expected",
    [
        ("user123", "read", "transactions", True),
        ("user123", "delete", "transactions/txn-456", False),
        ("user456", "read", "wallets/wallet-456", True),
        (
            "user789",
            "write",
            "wallets/wallet-456/transactions/txn-999",
            True,
        ),
        ("user789", "write", "wallets/wallet-789/transactions", True),
        ("admin789", "delete", "accounts/acc-123/settings", True),
        ("unknown-user", "read", "transactions", False),
    ],
)
def test_check_permission(user_id, action, resource, expected):
    assert check_permission(user_id, action, resource) is expected

def test_deny_overrides_more_specific_allow():
    from app.database import database_connection
    from app.services.authorization import resolve_permission

    user_id = "test-deny-user"
    action = "read"

    # Add a general deny and a more-specific allow.
    with database_connection() as connection:
        connection.execute(
            """
            DELETE FROM user_permissions
            WHERE user_id = ?
            """,
            (user_id,),
        )
        connection.executemany(
            """
            INSERT INTO user_permissions
                (user_id, action, resource, effect)
            VALUES (?, ?, ?, ?)
            """,
            [
                (user_id, action, "wallets/*", "deny"),
                (
                    user_id,
                    action,
                    "wallets/wallet-123/transactions",
                    "allow",
                ),
            ],
        )
        connection.commit()

    allowed, matched_permissions = resolve_permission(
        user_id=user_id,
        action=action,
        resource="wallets/wallet-123/transactions",
    )

    assert allowed is False
    assert matched_permissions
    assert all(
        permission["effect"] == "deny"
        for permission in matched_permissions
    )

    # Clean up the test data.
    with database_connection() as connection:
        connection.execute(
            "DELETE FROM user_permissions WHERE user_id = ?",
            (user_id,),
        )
        connection.commit()
