from datetime import datetime, timezone
from uuid import uuid4

TASK_ID = str(uuid4())
PARENT_ID = str(uuid4())
CHILD_ID = "22222222-2222-2222-2222-222222222222"
ASSIGNMENT_ID = str(uuid4())


def _task_row():
    return {
        "id": TASK_ID,
        "parent_id": PARENT_ID,
        "title": "Tender la cama",
        "description": "Tender la cama correctamente",
        "due_date": "2026-10-26",
        "due_time": "18:00:00",
        "reward_keys": 25,
        "duration_hours": 0,
        "duration_minutes": 10,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _assignment_row():
    return {
        "id": ASSIGNMENT_ID,
        "task_id": TASK_ID,
        "child_id": CHILD_ID,
        "status": "assigned",
        "assigned_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }


def test_mis_tareas_returns_assigned_tasks(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [[_task_row()], [_assignment_row()]]

    response = client.get("/tareas/mis-tareas", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Tender la cama"
    assert len(body[0]["assignments"]) == 1
    assert body[0]["assignments"][0]["status"] == "assigned"


def test_mis_tareas_empty_when_no_assignments(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [[]]

    response = client.get("/tareas/mis-tareas", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_mis_tareas_rejects_padre_token(client, padre_token):
    response = client.get("/tareas/mis-tareas", headers={"Authorization": f"Bearer {padre_token}"})

    assert response.status_code == 403


def test_mis_tareas_requires_auth(client):
    response = client.get("/tareas/mis-tareas")

    assert response.status_code in (401, 403)
