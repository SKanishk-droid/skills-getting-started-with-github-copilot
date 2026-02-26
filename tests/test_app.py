import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.fixture

def client():
    # reload the app module to reset in-memory state between tests
    import src.app as app_mod

    importlib.reload(app_mod)
    client = TestClient(app_mod.app)
    return client


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # each entry should have participants list
    for details in data.values():
        assert isinstance(details.get("participants"), list)


def test_signup_and_prevent_duplicate(client):
    new_email = "tester@mergington.edu"
    # choose a known activity
    activity = "Chess Club"
    # signup first time
    resp = client.post(f"/activities/{activity}/signup?email={new_email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # signups should include the new email exactly once
    resp = client.get("/activities")
    data = resp.json()
    participants = data[activity]["participants"]
    assert participants.count(new_email) == 1

    # duplicate signup should be rejected
    resp = client.post(f"/activities/{activity}/signup?email={new_email}")
    assert resp.status_code == 400
    assert "already" in resp.json().get("detail", "").lower()


def test_signup_nonexistent_activity(client):
    resp = client.post("/activities/NotThere/signup?email=foo@bar.com")
    assert resp.status_code == 404


def test_remove_participant(client):
    activity = "Chess Club"
    email = "michael@mergington.edu"
    # ensure present initially
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]

    resp = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp.status_code == 200
    assert "Removed" in resp.json().get("message", "")

    # verify removal
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_remove_nonexistent(client):
    activity = "Chess Club"
    resp = client.delete(f"/activities/{activity}/participants?email=noone@nowhere.edu")
    assert resp.status_code == 404


def test_remove_from_nonexistent_activity(client):
    resp = client.delete("/activities/Nope/participants?email=foo@bar.com")
    assert resp.status_code == 404
