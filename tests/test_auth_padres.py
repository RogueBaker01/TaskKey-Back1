from datetime import datetime, timezone
from uuid import uuid4

from app.utils.security import hash_password, verify_token

PADRE_ID = str(uuid4())


def _padre_row(**overrides):
    row = {
        "id": PADRE_ID,
        "nombre": "Ana",
        "apellido": "Lopez",
        "email": "ana@test.com",
        "password_hash": hash_password("secret123"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    row.update(overrides)
    return row


def test_register_padre_issues_role_padre_token(client, fake_conn):
    # 1) SELECT por email -> no existe; 2) INSERT ... RETURNING *
    fake_conn.cursor_obj._results = [None, _padre_row()]

    response = client.post(
        "/auth_padres/register",
        json={"nombre": "Ana", "apellido": "Lopez", "email": "ana@test.com", "password": "secret123"},
    )

    assert response.status_code == 201
    token = response.json()["access_token"]
    payload = verify_token(token)
    assert payload["role"] == "padre"


def test_register_padre_rejects_duplicate_email(client, fake_conn):
    fake_conn.cursor_obj._results = [_padre_row()]

    response = client.post(
        "/auth_padres/register",
        json={"nombre": "Ana", "apellido": "Lopez", "email": "ana@test.com", "password": "secret123"},
    )

    assert response.status_code == 400


def test_login_padre_issues_role_padre_token(client, fake_conn):
    fake_conn.cursor_obj._results = [_padre_row()]

    response = client.post("/auth_padres/login", json={"email": "ana@test.com", "password": "secret123"})

    assert response.status_code == 200
    token = response.json()["access_token"]
    payload = verify_token(token)
    assert payload["role"] == "padre"


def test_login_padre_wrong_password(client, fake_conn):
    fake_conn.cursor_obj._results = [_padre_row()]

    response = client.post("/auth_padres/login", json={"email": "ana@test.com", "password": "wrong"})

    assert response.status_code == 401


def test_get_me_padre_rejects_child_token(client, child_token):
    response = client.get("/auth_padres/me", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 403


def test_get_me_padre_success(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [_padre_row(), []]

    response = client.get("/auth_padres/me", headers={"Authorization": f"Bearer {padre_token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "ana@test.com"
