import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings


#conexión a la base de datos
def get_connection():

    return psycopg2.connect(
        host=settings.DB_ENDPOINT,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=RealDictCursor,
        connect_timeout=10,
    )


#conexión a la base de datos con yield
def get_db():
    conn = get_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
