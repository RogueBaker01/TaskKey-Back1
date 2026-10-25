from datetime import datetime, timedelta, timezone

from app.utils.security import hash_password

HIJO_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
PARENT_ID = "11111111-1111-1111-1111-111111111111"
CODIGO_PLANO = "ABC123XYZ9"


def _hijo_row(**overrides):
    row = {
        "id": HIJO_ID,
        "parent_id": PARENT_ID,
        "nombre": "Juanito",
        "apellido": "Perez",
        "genero": "M",
        "fecha_nacimiento": "2015-05-01",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "codigo_auth_hash": hash_password(CODIGO_PLANO),
        "code_expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }
    row.update(overrides)
    return row


def test_login_hijo_success(client, fake_conn):
    fake_conn.cursor_obj._results = [[_hijo_row()]]

    response = client.post("/auth_hijos/login", json={"codigo": CODIGO_PLANO})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["child"]["nombre"] == "Juanito"
    assert body["child"]["id"] == HIJO_ID
    # El codigo de vinculacion se invalida (se envia la query de UPDATE)
    assert fake_conn.committed is True


def test_login_hijo_wrong_code(client, fake_conn):
    fake_conn.cursor_obj._results = [[_hijo_row()]]

    response = client.post("/auth_hijos/login", json={"codigo": "codigo-incorrecto"})

    assert response.status_code == 401


def test_login_hijo_no_candidates(client, fake_conn):
    fake_conn.cursor_obj._results = [[]]

    response = client.post("/auth_hijos/login", json={"codigo": CODIGO_PLANO})

    assert response.status_code == 401


def test_get_me_hijo_success(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [_hijo_row()]

    response = client.get("/auth_hijos/me", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 200
    assert response.json()["nombre"] == "Juanito"


def test_get_me_hijo_not_found(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [None]

    response = client.get("/auth_hijos/me", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 404


def test_get_me_hijo_rejects_padre_token(client, padre_token):
    response = client.get("/auth_hijos/me", headers={"Authorization": f"Bearer {padre_token}"})

    assert response.status_code == 403


def test_get_me_hijo_requires_auth(client):
    response = client.get("/auth_hijos/me")

    assert response.status_code in (401, 403)
