import os, tempfile
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["SECRET_KEY"] = "test-secret"
for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_FROM_EMAIL", "BREVO_API_KEY"):
    os.environ[k] = ""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import seed_facilities


@pytest.fixture(scope="session")
def client():
    seed_facilities.run()
    return TestClient(app)


def make_user(client, email):
    r = client.post("/api/auth/register", json={"full_name": "Test User", "email": email, "password": "Passw0rdX"})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth(client, request):
    return make_user(client, f"{request.node.name}@example.com")
