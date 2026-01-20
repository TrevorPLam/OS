import json


def test_oauth_callback_rejects_missing_state(client):
    payload = {
        "provider": "google",
        "access_token": "test-access-token",
        "email": "missing-state@example.com",
    }

    response = client.post(
        "/api/v1/auth/oauth/callback/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid OAuth state"


def test_oauth_callback_rejects_mismatched_state(client):
    state_response = client.get("/api/v1/auth/oauth/state/")
    assert state_response.status_code == 200

    payload = {
        "provider": "google",
        "access_token": "test-access-token",
        "email": "mismatch-state@example.com",
        "state": "invalid-state",
    }

    response = client.post(
        "/api/v1/auth/oauth/callback/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid OAuth state"


def test_oauth_callback_accepts_valid_state_once(client):
    state_response = client.get("/api/v1/auth/oauth/state/")
    assert state_response.status_code == 200
    state_token = state_response.json()["state"]

    payload = {
        "provider": "google",
        "access_token": "test-access-token",
        "email": "valid-state@example.com",
        "state": state_token,
    }

    response = client.post(
        "/api/v1/auth/oauth/callback/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["message"] == "OAuth login successful"

    replay_response = client.post(
        "/api/v1/auth/oauth/callback/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert replay_response.status_code == 400
    assert replay_response.json()["error"] == "Invalid OAuth state"
