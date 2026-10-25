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
        {"duration_hours": 0, "duration_minutes": 20},
    ]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado",
        json={"status": "verified"},
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 200
    assert notified.get("usuario_id") == CHILD_ID
    assert notified.get("tipo") == "TAREA_CONFIRMADA"
    # Se ejecutaron: select assignment, update status, select duration, update device_policies
    assert len(fake_conn.cursor_obj.queries) == 4
    assert fake_conn.committed is True


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
