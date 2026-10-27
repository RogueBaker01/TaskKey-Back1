from uuid import uuid4

ASSIGNMENT_ID = str(uuid4())


def test_padre_desasigna_tarea(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [{"id": ASSIGNMENT_ID, "status": "assigned"}]

    response = client.delete(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}",
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 204
    assert fake_conn.committed is True


def test_desasignar_rechaza_asignacion_verificada(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [{"id": ASSIGNMENT_ID, "status": "verified"}]

    response = client.delete(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}",
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 409


def test_desasignar_not_found(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [None]

    response = client.delete(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}",
        headers={"Authorization": f"Bearer {padre_token}"},
    )

    assert response.status_code == 404


def test_desasignar_rejects_child_token(client, child_token):
    response = client.delete(
        f"/tareas/asignaciones/{ASSIGNMENT_ID}",
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 403
