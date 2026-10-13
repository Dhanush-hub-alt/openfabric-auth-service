
import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from app.config import (
    AUTH0_ALGORITHMS,
    AUTH0_AUDIENCE,
    AUTH0_DOMAIN,
)


class AuthenticationError(Exception):
    """Raised when an access token cannot be authenticated."""


def verify_access_token(token: str) -> dict:
    """
    Verify an Auth0 access token and return its trusted claims.

    Validates the signature, expiration, issuer, and audience.
    """
    if not AUTH0_DOMAIN or not AUTH0_AUDIENCE:
        raise RuntimeError(
            "AUTH0_DOMAIN and AUTH0_AUDIENCE must be configured."
        )

    if not token or not token.strip():
        raise AuthenticationError("Access token is missing.")

    if not AUTH0_ALGORITHMS:
        raise RuntimeError("AUTH0_ALGORITHMS must be configured.")

    issuer = f"https://{AUTH0_DOMAIN}/"
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"

    try:
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=issuer,
            options={
                "require": ["exp", "iss", "aud", "sub"],
            },
        )

        if not claims.get("sub"):
            raise AuthenticationError(
                "Access token does not contain a subject."
            )

        return claims

    except AuthenticationError:
        raise
    except PyJWTError as exc:
        raise AuthenticationError(
            "Invalid or expired access token."
        ) from exc
    except (OSError, ValueError) as exc:
        raise AuthenticationError(
            "Unable to retrieve or validate Auth0 signing keys."
        ) from exc