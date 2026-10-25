import os

# Los settings se leen al importar app.config, asi que hay que fijar las
# variables de entorno ANTES de importar cualquier modulo de la app. No se
# necesita una base de datos real: todos los tests reemplazan get_db con un
# fake en memoria.
os.environ.setdefault("DB_ENDPOINT", "localhost")
os.environ.setdefault("DB_NAME", "testdb")
os.environ.setdefault("DB_USER", "testuser")
os.environ.setdefault("DB_PASSWORD", "testpass")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("ALLOWED_ORIGINS", "*")
os.environ.setdefault("AZURE_NH_CONNECTION_STRING", "dummy")
os.environ.setdefault("AZURE_NH_NAME", "dummy")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.utils.security import create_access_token


class FakeCursor:
    """Cursor falso que responde con resultados pre-cargados en orden.

    `results` es una cola de valores que se van entregando en el orden en
    que el codigo de produccion llama a fetchone()/fetchall(). execute()
    solo registra la llamada para poder inspeccionarla en los tests.
    """

    def __init__(self, results=None):
        self._results = list(results or [])
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def _next(self):
        if not self._results:
            return None
        return self._results.pop(0)

    def fetchone(self):
        return self._next()

    def fetchall(self):
        value = self._next()
        return value if value is not None else []

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    """Conexion falsa que entrega un FakeCursor cargado con `results`."""

    def __init__(self, results=None):
        self.cursor_obj = FakeCursor(results)
        self.committed = False
        self.closed = False

    def cursor(self, *args, **kwargs):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def close(self):
        self.closed = True


@pytest.fixture
def fake_conn():
    """Conexion falsa vacia; los tests cargan `fake_conn.cursor_obj._results`."""
    return FakeConnection()


@pytest.fixture
def client(fake_conn):
    def override_get_db():
        yield fake_conn

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def padre_token():
    return create_access_token(data={"sub": "11111111-1111-1111-1111-111111111111", "email": "padre@test.com", "role": "padre"})


@pytest.fixture
def child_token():
    return create_access_token(data={"sub": "22222222-2222-2222-2222-222222222222", "role": "child"})


@pytest.fixture
def legacy_token_no_role():
    """Simula un token emitido antes de agregar el claim `role`."""
    return create_access_token(data={"sub": "33333333-3333-3333-3333-333333333333", "email": "legacy@test.com"})
