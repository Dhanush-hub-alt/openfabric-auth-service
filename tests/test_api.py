
import pytest
from fastapi.testclient import TestClient

import app.main as main


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client


def valid_request(**overrides):
    request_data = {
        "access_token": "test-token",
        "method": "GET",
        "path": "/transactions",
    }
    request_data.update(overrides)
    return request_data


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
        json=valid_request(),
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
        json=valid_request(access_token="invalid-token"),
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_authorize_rejects_blank_token(client):
    response = client.post(
        "/authorize",
        json=valid_request(access_token="   "),
    )

    assert response.status_code == 401


def test_authorize_rejects_missing_token_identity(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        main,
        "verify_access_token",
        lambda token: {"aud": "test-audience"},
    )

    response = client.post(
        "/authorize",
        json=valid_request(),
    )

    assert response.status_code == 401


def test_authorize_rejects_unsupported_method(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        main,
        "verify_access_token",
        lambda token: {"sub": "user123"},
    )

    response = client.post(
        "/authorize",
        json=valid_request(method="HEAD"),
    )

    assert response.status_code == 400


def test_authorize_rejects_blank_path(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "verify_access_token",
        lambda token: {"sub": "user123"},
    )

    response = client.post(
        "/authorize",
        json=valid_request(path=" / "),
    )

    assert response.status_code == 400


def test_authorize_requires_request_fields(client):
    response = client.post(
        "/authorize",
        json={"method": "GET", "path": "/transactions"},
    )

    assert response.status_code == 422


def test_authorize_rejects_malformed_request_body(client):
    response = client.post(
        "/authorize",
        content="{invalid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422