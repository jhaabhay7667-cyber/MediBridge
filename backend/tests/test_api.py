import jwt, os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from .conftest import make_user

EM = {"incident_type": "Accident", "patient_name": "Test Patient", "priority": "CRITICAL",
      "latitude": 22.57, "longitude": 88.36}


def test_register_login_me(client):
    h = make_user(client, "a@example.com")
    assert client.get("/api/auth/me", headers=h).json()["email"] == "a@example.com"
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "Passw0rdX"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/register", json={"full_name": "x", "email": "a@example.com", "password": "Passw0rdX"}).status_code == 409


def test_protected_and_bad_tokens(client):
    assert client.get("/api/emergencies").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401
    expired = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, "test-secret", algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_emergency_crud_and_isolation(client, auth):
    r = client.post("/api/emergencies", json=EM, headers=auth)
    assert r.status_code == 201 and r.json()["code"].startswith("MB-")
    eid = r.json()["id"]
    assert client.patch(f"/api/emergencies/{eid}", json={"status": "RESOLVED"}, headers=auth).json()["status"] == "RESOLVED"
    events = [e["event"] for e in client.get(f"/api/emergencies/{eid}/timeline", headers=auth).json()]
    assert "Emergency created" in events
    other = make_user(client, "other@example.com")
    assert client.get(f"/api/emergencies/{eid}", headers=other).status_code == 404
    assert client.delete(f"/api/emergencies/{eid}", headers=auth).status_code == 204
    assert client.get(f"/api/emergencies/{eid}", headers=auth).status_code == 404


def test_invalid_input(client, auth):
    assert client.post("/api/emergencies", json={**EM, "latitude": 999}, headers=auth).status_code == 422
    assert client.post("/api/emergencies", json={**EM, "incident_type": "Nope"}, headers=auth).status_code == 422


def test_contacts_and_notify(client, auth):
    em = client.post("/api/emergencies", json=EM, headers=auth).json()
    assert client.post(f"/api/emergencies/{em['id']}/notify", headers=auth).status_code == 400  # no contacts
    c = client.post("/api/contacts", json={"name": "Rahul", "email": "r@example.com", "is_primary": True}, headers=auth)
    assert c.status_code == 201
    cid = c.json()["id"]
    assert client.put(f"/api/contacts/{cid}", json={"name": "Rahul K", "email": "r@example.com"}, headers=auth).json()["name"] == "Rahul K"
    # SMTP not configured -> honest 502 and a FAILED notification record
    assert client.post(f"/api/emergencies/{em['id']}/notify", headers=auth).status_code == 502
    notes = client.get(f"/api/emergencies/{em['id']}/notifications", headers=auth).json()
    assert any(n["status"] == "FAILED" for n in notes)
    # SMTP success (mocked)
    with patch("app.routers.emergencies.send_email", return_value=(True, None, 1)):
        assert client.post(f"/api/emergencies/{em['id']}/notify", headers=auth).status_code == 200
    assert client.delete(f"/api/contacts/{cid}", headers=auth).status_code == 204


def test_facilities(client, auth):
    assert len(client.get("/api/facilities", headers=auth).json()) >= 5
    near = client.get("/api/facilities/nearby?lat=22.57&lon=88.36&radius_km=10", headers=auth).json()
    assert near and near == sorted(near, key=lambda f: f["distance_km"])
    assert client.get("/api/facilities/nearby?lat=200&lon=0", headers=auth).status_code == 422
    assert client.get("/api/facilities/nearby/search?lat=22.57&lon=88.36&type=Blood%20Bank", headers=auth).status_code == 200


def test_coordination(client, auth):
    em = client.post("/api/emergencies", json=EM, headers=auth).json()
    fid = client.get("/api/facilities", headers=auth).json()[0]["id"]
    assert client.post(f"/api/emergencies/{em['id']}/hospital?facility_id={fid}", headers=auth).json()["hospital"]["status"] == "REQUESTED"
    r = client.patch(f"/api/emergencies/{em['id']}/coordination", json={"ambulance_status": "ASSIGNED"}, headers=auth)
    assert r.json()["ambulance"]["status"] == "ASSIGNED"
    assert client.patch(f"/api/emergencies/{em['id']}/coordination", json={"hospital_status": "BOGUS"}, headers=auth).status_code == 422


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
