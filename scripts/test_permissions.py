
from app.services.authorization import get_action, check_permission


def main():
    tests = [
        # Existing tests
        ("user123", "GET", "transactions", True),
        ("user123", "DELETE", "transactions/txn-456", False),
        ("user456", "GET", "wallets/wallet-789/transactions", True),
        ("user456", "POST", "wallets/wallet-789", True),
        ("user456", "POST", "wallets/wallet-456", False),

        # Wildcard and admin tests
        ("user456", "GET", "wallets/wallet-456", True),
        ("user789", "POST", "wallets/wallet-456/transactions/txn-999", True),
        ("user789", "POST", "wallets/wallet-789/transactions", False),
        ("admin789", "DELETE", "accounts/acc-123/settings", True),
    ]

    failures = 0

    for user_id, method, resource, expected in tests:
        action = get_action(method)
        actual = (
            check_permission(user_id, action, resource)
            if action is not None
            else False
        )

        result = "PASS" if actual == expected else "FAIL"
        if actual != expected:
            failures += 1

        print(
            "{}: {} {} -> expected={}, actual={}".format(
                result, method, resource, expected, actual
            )
        )

    print("\nTotal: {} tests, {} failures".format(len(tests), failures))


if __name__ == "__main__":
    main()