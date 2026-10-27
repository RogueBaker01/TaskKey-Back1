from datetime import datetime, timedelta, timezone


def _completado_hace(dias):
    # psycopg2/RealDictCursor devuelve datetime reales para columnas TIMESTAMPTZ, no strings
    return {"completed_at": datetime.now(timezone.utc) - timedelta(days=dias)}


def test_progreso_sin_tareas_completadas(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [[]]

    response = client.get("/tareas/mi-progreso", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "total_completadas": 0,
        "completadas_semana": 0,
        "racha_actual": 0,
        "racha_mas_larga": 0,
    }


def test_progreso_racha_actual_de_3_dias(client, fake_conn, child_token):
    # Completo tareas hoy, ayer y anteayer -> racha actual de 3
    fake_conn.cursor_obj._results = [[
        _completado_hace(2),
        _completado_hace(1),
        _completado_hace(0),
    ]]

    response = client.get("/tareas/mi-progreso", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_completadas"] == 3
    assert body["racha_actual"] == 3
    assert body["racha_mas_larga"] == 3
    assert body["completadas_semana"] == 3


def test_progreso_racha_actual_se_rompe_si_no_hubo_nada_ayer(client, fake_conn, child_token):
    # Completo hace 5 y 4 dias (racha vieja de 2) pero nada reciente -> racha actual 0
    fake_conn.cursor_obj._results = [[
        _completado_hace(5),
        _completado_hace(4),
    ]]

    response = client.get("/tareas/mi-progreso", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["racha_actual"] == 0
    assert body["racha_mas_larga"] == 2


def test_progreso_rejects_padre_token(client, padre_token):
    response = client.get("/tareas/mi-progreso", headers={"Authorization": f"Bearer {padre_token}"})

    assert response.status_code == 403
