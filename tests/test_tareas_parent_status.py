from datetime import datetime, timezone
from uuid import uuid4

import app.routers.tareas as tareas_router

ASSIGNMENT_ID = str(uuid4())
TASK_ID = str(uuid4())
CHILD_ID = str(uuid4())


def _assignment_row(status):
    return {
        "id": ASSIGNMENT_ID,
        "task_id": TASK_ID,
        "child_id": CHILD_ID,
        "status": status,
        "assigned_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }


def test_parent_verifies_task_awards_screen_time_and_notifies_child(client, fake_conn, padre_token, monkeypatch):
    notified = {}
    monkeypatch.setattr(
        tareas_router,
        "enviar_notificacion",
        lambda **kwargs: notified.update(kwargs),
    )

    fake_conn.cursor_obj._results = [
        _assignment_row("completed"),
        _assignment_row("verified"),
        {"duration_hours": 0, "duration_minutes": 20, "reward_keys": 25},
    ]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado",
        json={"status": "verified"},
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 200
    assert notified.get("usuario_id") == CHILD_ID
    assert notified.get("tipo") == "TAREA_CONFIRMADA"
    # select assignment, update status, select duration/llaves, select children FOR UPDATE,
    # ensure_device_policy, update device_policies, update llaves, update earned_keys/minutes
    assert len(fake_conn.cursor_obj.queries) == 8
    llaves_query, llaves_params = fake_conn.cursor_obj.queries[-2]
    assert "llaves_disponibles" in llaves_query
    assert 25 in llaves_params
    assert fake_conn.committed is True


def test_parent_verifies_task_skips_key_award_when_task_has_no_keys(client, fake_conn, padre_token, monkeypatch):
    monkeypatch.setattr(tareas_router, "enviar_notificacion", lambda **kwargs: None)

    fake_conn.cursor_obj._results = [
        _assignment_row("completed"),
        _assignment_row("verified"),
        {"duration_hours": 0, "duration_minutes": 0, "reward_keys": 0},
    ]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado",
        json={"status": "verified"},
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 200
    # select assignment, update status, select duration/llaves -> nada mas (sin tiempo ni llaves que acreditar)
    assert len(fake_conn.cursor_obj.queries) == 4


def test_parent_does_not_renotify_already_verified_task(client, fake_conn, padre_token, monkeypatch):
    notified = {}
    monkeypatch.setattr(
        tareas_router,
        "enviar_notificacion",
        lambda **kwargs: notified.update(kwargs),
    )

    fake_conn.cursor_obj._results = [
        _assignment_row("verified"),
        _assignment_row("verified"),
    ]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado",
        json={"status": "verified"},
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 200
    assert notified == {}


def test_parent_status_update_invalid_status(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [_assignment_row("assigned")]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado",
        json={"status": "no-existe"},
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 400


def test_parent_status_update_not_found(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [None]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado",
        json={"status": "verified"},
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 404


def test_parent_status_update_rejects_child_token(client, child_token):
    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado",
        json={"status": "verified"},
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 403


def test_verified_cannot_be_reopened(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [_assignment_row("verified")]
    response = client.put(f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado", json={"status": "in_progress"}, headers={"Authorization": f"Bearer {padre_token}"})
    assert response.status_code == 409
    assert len(fake_conn.cursor_obj.queries) == 1
    assert "FOR UPDATE" in fake_conn.cursor_obj.queries[0][0]


def test_cannot_verify_unfinished_task(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [_assignment_row("assigned")]
    response = client.put(f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado", json={"status": "verified"}, headers={"Authorization": f"Bearer {padre_token}"})
    assert response.status_code == 409
