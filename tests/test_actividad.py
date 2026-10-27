from datetime import datetime, timezone
import pytest

CHILD = '22222222-2222-2222-2222-222222222222'
PARENT = '11111111-1111-1111-1111-111111111111'

def headers(token):
    return {'Authorization': f'Bearer {token}'}

def perfil():
    return {'id': CHILD, 'parent_id': PARENT, 'nombre': 'Hijo', 'created_at': datetime.now(timezone.utc), 'llaves_disponibles': 25, 'avatar_id': 'capifer'}


def test_summary_reads_balance_and_progress_for_authenticated_child(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [perfil(), {'available_screen_time_minutes': 20}, [{'completed_at': datetime.now(timezone.utc)}]]
    response = client.get('/actividad/mi-resumen', headers=headers(child_token))
    assert response.status_code == 200
    data = response.json()
    assert data['perfil']['llaves_disponibles'] == 25
    assert data['perfil']['avatar_id'] == 'capifer'
    assert data['progreso']['racha_actual'] == 1
    assert all(query[1][0] == CHILD for query in fake_conn.cursor_obj.queries)


def test_rewards_use_persisted_balance_and_earned_values(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [{'llaves_disponibles': 25}, {'available_screen_time_minutes': 20}, [{'id': CHILD, 'title': 'Misión', 'keys': 25, 'minutes': 20}]]
    data = client.get('/actividad/mis-recompensas', headers=headers(child_token)).json()
    assert data['llaves'] == 25
    assert data['minutos'] == 20
    assert data['historial'][0]['keys'] == 25
    assert 'ta.earned_keys' in fake_conn.cursor_obj.queries[-1][0]
    assert "ta.status = 'verified'" in fake_conn.cursor_obj.queries[-1][0]


def test_no_history_does_not_invent_achievements(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [[]]
    data = client.get('/actividad/mis-logros', headers=headers(child_token)).json()
    assert len(data) == 3
    assert all(item['obtenido'] is False and item['actual'] == 0 for item in data)


def test_monthly_progress_fills_missing_months_without_sample_values(client, fake_conn, child_token):
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    fake_conn.cursor_obj._results = [[{'mes': month, 'asignadas': 4, 'completadas': 3}]]
    data = client.get('/actividad/mi-progreso-mensual', headers=headers(child_token)).json()
    assert len(data) == 3
    assert data[-1]['cumplimiento'] == 75
    assert data[0]['asignadas'] == data[0]['completadas'] == data[0]['cumplimiento'] == 0


def test_avatar_is_persisted_for_current_child(client, fake_conn, child_token):
    fake_conn.cursor_obj._results = [perfil()]
    response = client.put('/actividad/mi-avatar', json={'avatar_id': 'capifer'}, headers=headers(child_token))
    assert response.status_code == 200
    assert response.json()['avatar_id'] == 'capifer'
    assert fake_conn.committed
    assert fake_conn.cursor_obj.queries[0][1] == ('capifer', CHILD)


def test_unknown_avatar_rejected_before_db_write(client, fake_conn, child_token):
    response = client.put('/actividad/mi-avatar', json={'avatar_id': 'invalid'}, headers=headers(child_token))
    assert response.status_code == 400
    assert not fake_conn.cursor_obj.queries


@pytest.mark.parametrize('path', ['mi-resumen', 'mis-recompensas', 'mis-logros', 'mi-progreso-mensual', 'avatares'])
def test_child_data_rejects_parent_role(client, padre_token, path):
    assert client.get('/actividad/' + path, headers=headers(padre_token)).status_code == 403
