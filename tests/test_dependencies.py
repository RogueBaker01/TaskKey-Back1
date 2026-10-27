import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.utils.dependencies import get_current_user, get_current_child, get_current_actor
from app.utils.security import create_access_token


def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_accepts_padre_token():
    token = create_access_token(data={"sub": "padre-1", "email": "a@a.com", "role": "padre"})
    user = get_current_user(_creds(token))
    assert user == {"id": "padre-1", "email": "a@a.com"}


def test_get_current_user_accepts_legacy_token_without_role():
    token = create_access_token(data={"sub": "padre-1", "email": "a@a.com"})
    user = get_current_user(_creds(token))
    assert user["id"] == "padre-1"


def test_get_current_user_rejects_child_token():
    token = create_access_token(data={"sub": "child-1", "role": "child"})
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_creds(token))
    assert exc_info.value.status_code == 403


def test_get_current_user_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(_creds("not-a-valid-token"))
    assert exc_info.value.status_code == 401


def test_get_current_child_accepts_child_token():
    token = create_access_token(data={"sub": "child-1", "role": "child"})
    child = get_current_child(_creds(token))
    assert child == {"id": "child-1", "role": "child"}


def test_get_current_child_rejects_padre_token():
    token = create_access_token(data={"sub": "padre-1", "email": "a@a.com", "role": "padre"})
    with pytest.raises(HTTPException) as exc_info:
        get_current_child(_creds(token))
    assert exc_info.value.status_code == 403


def test_get_current_child_rejects_legacy_token_without_role():
    token = create_access_token(data={"sub": "padre-1", "email": "a@a.com"})
    with pytest.raises(HTTPException) as exc_info:
        get_current_child(_creds(token))
    assert exc_info.value.status_code == 403


def test_get_current_actor_accepts_padre_token():
    token = create_access_token(data={"sub": "padre-1", "email": "a@a.com", "role": "padre"})
    actor = get_current_actor(_creds(token))
    assert actor == {"id": "padre-1", "role": "padre"}


def test_get_current_actor_accepts_child_token():
    token = create_access_token(data={"sub": "child-1", "role": "child"})
    actor = get_current_actor(_creds(token))
    assert actor == {"id": "child-1", "role": "child"}


def test_get_current_actor_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        get_current_actor(_creds("garbage"))
    assert exc_info.value.status_code == 401
