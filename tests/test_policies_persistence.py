from datetime import datetime, timezone
from tests.test_actividad import CHILD, PARENT, headers


def policy(**changes):
    return {'id': PARENT, 'child_id': CHILD, 'available_screen_time_minutes': 0,
            'sleep_start_time': '21:30:00', 'sleep_end_time': '07:30:00', 'sleep_days': 'Lun,Mar',
            'restricted_apps': [], 'created_at': datetime.now(timezone.utc), 'updated_at': datetime.now(timezone.utc), **changes}


def test_get_missing_policy_commits_creation(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [{'id': CHILD}, None, policy()]
    response = client.get(f'/policies/{CHILD}', headers=headers(padre_token))
    assert response.status_code == 200
    assert fake_conn.committed


def test_disabled_schedule_is_saved_without_resetting_other_fields(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [{'id': CHILD}, policy(sleep_enabled=False)]
    response = client.put(f'/policies/{CHILD}', json={'sleep_enabled': False}, headers=headers(padre_token))
    assert response.status_code == 200
    assert response.json()['sleep_enabled'] is False
    update, params = fake_conn.cursor_obj.queries[-1]
    assert 'sleep_enabled = %s' in update
    assert 'restricted_apps =' not in update
    assert fake_conn.committed


def test_unknown_app_is_rejected(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [{'id': CHILD}]
    response = client.put(f'/policies/{CHILD}', json={'restricted_apps': ['invalid']}, headers=headers(padre_token))
    assert response.status_code == 400
    assert not fake_conn.committed


def test_other_family_policy_is_forbidden(client, fake_conn, padre_token):
    fake_conn.cursor_obj._results = [None]
    assert client.get(f'/policies/{CHILD}', headers=headers(padre_token)).status_code == 403
