import pytest
from fastapi.testclient import TestClient

import app.main as main


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_authorize_with_valid_token(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "verify_access_token",
        lambda token: {"sub": "user123"},
    )

    response = client.post(
        "/authorize",
        json={
            "access_token": "test-token",
            "method": "GET",
            "path": "/transactions",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "ALLOW"
    assert body["user_id"] == "user123"
    assert "reason" in body
    assert isinstance(body["matched_permissions"], list)


def test_authorize_rejects_invalid_token(client, monkeypatch):
    def reject_token(token):
        raise main.AuthenticationError("Invalid token")

    monkeypatch.setattr(main, "verify_access_token", reject_token)

    response = client.post(
        "/authorize",
        json={
            "access_token": "invalid-token",
            "method": "GET",
            "path": "/transactions",
        },
    )

    assert response.status_code == 401


def test_authorize_rejects_unsupported_method(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "verify_access_token",
        lambda token: {"sub": "user123"},
    )

    response = client.post(
        "/authorize",
        json={
            "access_token": "test-token",
            "method": "HEAD",
            "path": "/transactions",
        },
    )

    assert response.status_code == 400


def test_authorize_requires_request_fields(client):
    response = client.post(
        "/authorize",
        json={"method": "GET", "path": "/transactions"},
    )

    assert response.status_code == 422
