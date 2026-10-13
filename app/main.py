from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import APP_NAME
from app.database import initialize_database
from app.auth.jwt_verifier import (
    AuthenticationError,
    verify_access_token,
)
from app.services.authorization import (
    get_action,
    resolve_permission,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title=APP_NAME,
    description="OAuth2 authentication and authorization service",
    version="0.1.0",
    lifespan=lifespan,
)


class AuthorizationRequest(BaseModel):
    access_token: str
    method: str
    path: str


class MatchedPermission(BaseModel):
    action: str
    resource: str
    effect: str


class AuthorizationResponse(BaseModel):
    decision: str
    user_id: str
    reason: str
    matched_permissions: List[MatchedPermission]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post(
    "/authorize",
    response_model=AuthorizationResponse,
)
def authorize(request: AuthorizationRequest):
    if not request.access_token.strip():
        raise HTTPException(
            status_code=401,
            detail="Access token is required",
        )

    try:
        claims = verify_access_token(request.access_token)
    except AuthenticationError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token does not contain a user identity",
        )

    action = get_action(request.method)
    if action is None:
        raise HTTPException(
            status_code=400,
            detail="Unsupported HTTP method",
        )

    resource = request.path.strip("/")
    if not resource:
        raise HTTPException(
            status_code=400,
            detail="Path must identify a resource",
        )

    allowed, matched_permissions = resolve_permission(
        user_id=user_id,
        action=action,
        resource=resource,
    )

    decision = "ALLOW" if allowed else "DENY"

    if allowed:
        reason = (
            "User has {} permission for {}".format(
                action, resource
            )
        )
    elif matched_permissions:
        reason = (
            "Matching permission rules do not allow {} on {}".format(
                action, resource
            )
        )
    else:
        reason = (
            "No matching permission found for {} on {}".format(
                action, resource
            )
        )

    return {
        "decision": decision,
        "user_id": user_id,
        "reason": reason,
        "matched_permissions": matched_permissions,
    }
