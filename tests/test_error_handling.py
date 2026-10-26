"""
Pruebas que DEMUESTRAN (no solo asumen) como se comporta el backend cuando
Postgres lanza un error real a mitad de un request -- el caso que mas importa
antes de una demo: una migracion que no se corrio, una columna que no existe,
una conexion que se cae, etc.
"""
import psycopg2
import pytest

import app.database as database_module
from tests.conftest import FakeConnection


def test_get_db_hace_rollback_y_cierra_la_conexion_si_el_handler_falla(monkeypatch):
    """
    Prueba app.database.get_db directamente (sin pasar por el override de
    los tests), para probar el rollback real que usa produccion.
    """
    fake = FakeConnection()
    monkeypatch.setattr(database_module, "get_connection", lambda: fake)

    generador = database_module.get_db()
    conn = next(generador)
    assert conn is fake
    assert fake.rolled_back is False

    with pytest.raises(ValueError):
        # Simula que el handler lanzo una excepcion mientras tenia la conexion abierta
        generador.throw(ValueError("columna no existe"))

    assert fake.rolled_back is True
    assert fake.closed is True


def test_error_real_de_postgres_no_crashea_el_proceso_y_devuelve_500_limpio(
    client_like_production, fake_conn, padre_token
):
    """
    Si una migracion no se corrio, psycopg2 lanza UndefinedColumn (subclase de
    psycopg2.Error) a mitad del cursor.execute(). Este test prueba que ese
    error real no se propaga como un traceback crudo al cliente: el manejador
    global de app/main.py lo atrapa y responde un 500 con un mensaje limpio.

    (Usa client_like_production porque el TestClient por defecto vuelve a
    lanzar la excepcion hacia el test en vez de dejar que el exception_handler
    responda -- eso solo pasa en tests, uvicorn real siempre usa el handler.)
    """
    fake_conn.cursor_obj.error_on_execute = psycopg2.errors.UndefinedColumn(
        'column "llaves_disponibles" does not exist'
    )

    response = client_like_production.get("/tareas/", headers={"Authorization": f"Bearer {padre_token}"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Ocurrió un error inesperado. Intenta de nuevo en unos segundos."}


def test_error_real_de_postgres_en_distintos_routers(client_like_production, fake_conn, padre_token, child_token):
    """Mismo chequeo en un par de rutas mas, para no confiar en un solo caso."""
    fake_conn.cursor_obj.error_on_execute = psycopg2.OperationalError("server closed the connection unexpectedly")

    response = client_like_production.get("/hijos/", headers={"Authorization": f"Bearer {padre_token}"})
    assert response.status_code == 500

    fake_conn.cursor_obj.error_on_execute = psycopg2.errors.UndefinedColumn('column "avatar_id" does not exist')
    response = client_like_production.get("/auth_hijos/me", headers={"Authorization": f"Bearer {child_token}"})
    assert response.status_code == 500
