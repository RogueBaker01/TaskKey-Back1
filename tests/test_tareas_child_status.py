from datetime import datetime, timezone
from uuid import uuid4

import app.routers.tareas as tareas_router

ASSIGNMENT_ID = str(uuid4())
TASK_ID = str(uuid4())
CHILD_ID = "22222222-2222-2222-2222-222222222222"
PARENT_ID = str(uuid4())


def _assignment_row(status):
    return {
        "id": ASSIGNMENT_ID,
        "task_id": TASK_ID,
        "child_id": CHILD_ID,
        "status": status,
        "assigned_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }


def test_child_marks_task_in_progress(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [
        _assignment_row("assigned"),
        _assignment_row("in_progress"),
    ]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado/child",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_child_marks_task_completed_notifies_parent(client, fake_conn, child_token, monkeypatch):
    notified = {}
    monkeypatch.setattr(
        tareas_router,
        "enviar_notificacion",
        lambda **kwargs: notified.update(kwargs),
    )

    fake_conn.cursor_obj._results = [
        _assignment_row("in_progress"),
        _assignment_row("completed"),
        {"parent_id": PARENT_ID},
    ]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado/child",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 200
    assert notified.get("usuario_id") == PARENT_ID
    assert notified.get("tipo") == "TAREA_COMPLETADA"


def test_child_cannot_set_verified_status(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [_assignment_row("assigned")]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado/child",
        json={"status": "verified"},
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 400


def test_child_status_update_not_found(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [None]

    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado/child",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 404


def test_child_status_update_rejects_padre_token(client, padre_token):
    response = client.put(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}/estado/child",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 403
