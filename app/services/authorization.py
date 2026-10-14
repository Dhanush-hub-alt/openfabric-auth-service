
from app.database import database_connection


# Map HTTP methods to permission actions.
ACTION_MAP = {
    "GET": "read",
    "POST": "write",
    "PUT": "write",
    "PATCH": "write",
    "DELETE": "delete",
}


def get_action(http_method: str):
    """Return the permission action for an HTTP method."""
    return ACTION_MAP.get(http_method.upper())


def normalize_resource(resource: str) -> str:
    """Remove leading and trailing slashes from a resource path."""
    return resource.strip("/")


def resource_matches(pattern: str, resource: str) -> bool:
    """
    Check whether a resource matches a permission pattern.

    A '*' wildcard matches zero or more path segments.
    Literal path segments must match exactly.

    Examples:
        wallets/* matches wallets/wallet-789
        wallets/*/transactions matches wallets/wallet-789/transactions
        wallets/*/transactions/* matches
            wallets/wallet-789/transactions/txn-123
        * matches any non-empty resource path
    """
    pattern = normalize_resource(pattern)
    resource = normalize_resource(resource)

    if not pattern or not resource:
        return pattern == resource

    if pattern == "*":
        return True

    pattern_parts = pattern.split("/")
    resource_parts = resource.split("/")

    def match_parts(pattern_index: int, resource_index: int) -> bool:
        # Both pattern and resource must be fully consumed.
        if pattern_index == len(pattern_parts):
            return resource_index == len(resource_parts)

        part = pattern_parts[pattern_index]

        if part == "*":
            # Try matching zero or more resource segments.
            for next_index in range(
                resource_index,
                len(resource_parts) + 1,
            ):
                if match_parts(pattern_index + 1, next_index):
                    return True
            return False

        if resource_index >= len(resource_parts):
            return False

        if part != resource_parts[resource_index]:
            return False

        return match_parts(pattern_index + 1, resource_index + 1)

    return match_parts(0, 0)


def permission_specificity(pattern: str):
    """
    Return a tuple used to compare resource-pattern specificity.

    Patterns with more literal segments are considered more specific.
    The number of segments and literal characters break ties.
    """
    normalized_pattern = normalize_resource(pattern)

    if not normalized_pattern:
        return 0, 0, 0

    parts = normalized_pattern.split("/")

    literal_segments = sum(
        1 for part in parts if part != "*"
    )

    literal_characters = sum(
        len(part) for part in parts if part != "*"
    )

    return literal_segments, len(parts), literal_characters


def resolve_permission(user_id: str, action: str, resource: str):
    """
    Resolve permissions for a user, action, and resource.

    Rules:
    1. Only permissions for the requested user and action are considered.
    2. Resource patterns must match the requested resource.
    3. The most-specific matching pattern takes precedence.
    4. If equally specific matching rules conflict, deny wins.
    5. If no permission matches, access is denied.

    Returns:
        (allowed, matched_permissions)
    """
    resource = normalize_resource(resource)

    if not resource:
        return False, []

    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT action, resource, effect
            FROM user_permissions
            WHERE user_id = ? AND action = ?
            """,
            (user_id, action),
        ).fetchall()

    matching_rows = [
        row
        for row in rows
        if resource_matches(row["resource"], resource)
    ]

    # No matching permission means default deny.
    if not matching_rows:
        return False, []

    # Select the most-specific matching resource patterns first.
    highest_specificity = max(
        permission_specificity(row["resource"])
        for row in matching_rows
    )

    selected_rows = [
        row
        for row in matching_rows
        if permission_specificity(row["resource"])
        == highest_specificity
    ]

    # Deny wins if equally specific rules conflict.
    has_deny = any(
        row["effect"] == "deny"
        for row in selected_rows
    )

    allowed = not has_deny and all(
        row["effect"] == "allow"
        for row in selected_rows
    )

    matched_permissions = [
        {
            "action": row["action"],
            "resource": row["resource"],
            "effect": row["effect"],
        }
        for row in selected_rows
    ]

    return allowed, matched_permissions


def check_permission(user_id: str, action: str, resource: str) -> bool:
    """Return whether the user is authorized for the requested resource."""
    allowed, _ = resolve_permission(user_id, action, resource)
    return allowed
