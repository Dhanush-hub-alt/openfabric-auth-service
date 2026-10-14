
import pytest

from app.services.authorization import (
    check_permission,
    get_action,
    resolve_permission,
    resource_matches,
)


@pytest.mark.parametrize(
    ("method", "expected_action"),
    [
        ("GET", "read"),
        ("POST", "write"),
        ("PUT", "write"),
        ("PATCH", "write"),
        ("DELETE", "delete"),
        ("HEAD", None),
    ],
)
def test_get_action(method, expected_action):
    assert get_action(method) == expected_action


@pytest.mark.parametrize(
    ("user_id", "action", "resource", "expected"),
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
        (
            "user789",
            "write",
            "wallets/wallet-789/transactions",
            True,
        ),
        (
            "admin789",
            "delete",
            "accounts/acc-123/settings",
            True,
        ),
        ("unknown-user", "read", "transactions", False),
    ],
)
def test_check_permission(user_id, action, resource, expected):
    assert check_permission(user_id, action, resource) is expected


def test_more_specific_allow_overrides_general_deny():
    from app.database import database_connection

    user_id = "test-specificity-user"
    action = "read"

    with database_connection() as connection:
        connection.execute(
            "DELETE FROM user_permissions WHERE user_id = ?",
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

    try:
        allowed, matched = resolve_permission(
            user_id,
            action,
            "wallets/wallet-123/transactions",
        )

        assert allowed is True
        assert len(matched) == 1
        assert matched[0]["resource"] == (
            "wallets/wallet-123/transactions"
        )
        assert matched[0]["effect"] == "allow"
    finally:
        with database_connection() as connection:
            connection.execute(
                "DELETE FROM user_permissions WHERE user_id = ?",
                (user_id,),
            )
            connection.commit()


def test_deny_wins_for_equally_specific_rules():
    from app.database import database_connection

    user_id = "test-equal-specificity-user"
    action = "read"
    resource = "wallets/wallet-123"

    with database_connection() as connection:
        connection.execute(
            "DELETE FROM user_permissions WHERE user_id = ?",
            (user_id,),
        )
        connection.executemany(
            """
            INSERT INTO user_permissions
                (user_id, action, resource, effect)
            VALUES (?, ?, ?, ?)
            """,
            [
                (user_id, action, resource, "allow"),
                (user_id, action, resource, "deny"),
            ],
        )
        connection.commit()

    try:
        allowed, matched = resolve_permission(
            user_id,
            action,
            resource,
        )

        assert allowed is False
        assert len(matched) == 2
        assert {permission["effect"] for permission in matched} == {
            "allow",
            "deny",
        }
    finally:
        with database_connection() as connection:
            connection.execute(
                "DELETE FROM user_permissions WHERE user_id = ?",
                (user_id,),
            )
            connection.commit()


def test_wildcard_matches_nested_resource():
    assert resource_matches(
        "wallets/*",
        "wallets/wallet-456/transactions",
    )


def test_wildcard_matches_resource_without_trailing_segment():
    assert resource_matches(
        "wallets/*/transactions/*",
        "wallets/wallet-789/transactions",
    )


def test_wildcard_matches_transaction_id():
    assert resource_matches(
        "wallets/*/transactions/*",
        "wallets/wallet-789/transactions/txn-999",
    )


def test_wildcard_does_not_match_different_prefix():
    assert not resource_matches(
        "wallets/*",
        "accounts/acc-123",
    )


def test_unknown_resource_defaults_to_deny():
    assert check_permission(
        "unknown-user",
        "read",
        "accounts/acc-123",
    ) is False