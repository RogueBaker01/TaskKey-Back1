import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_padres, auth_hijos, hijos, tareas, policies, notificaciones, actividad
from app.config import settings
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.utils.limiter import limiter

logger = logging.getLogger("taskkey")

app = FastAPI(
    title="TaskKey API",
    version="1.0.0",
    description="Backend API for TaskKey",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # type: ignore


@app.exception_handler(Exception)
async def manejador_de_errores_no_controlados(request: Request, exc: Exception):
    """
    Red de seguridad para cualquier excepcion que un router no haya capturado
    (p.ej. un error real de psycopg2 porque falto correr una migracion). El
    rollback de la transaccion ya ocurre en app.database.get_db antes de que
    la excepcion llegue hasta aqui; esto solo evita que el cliente reciba un
    traceback crudo y deja un registro con el que se pueda diagnosticar.
    """
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error inesperado. Intenta de nuevo en unos segundos."},
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(',')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Sin esto, el default_limits=["100/minute"] de app/utils/limiter.py nunca se
# aplicaba: solo funcionaban los @limiter.limit(...) puestos a mano en cada ruta.
app.add_middleware(SlowAPIMiddleware)
#routers
app.include_router(auth_padres.router)
app.include_router(auth_hijos.router)
app.include_router(hijos.router)
app.include_router(tareas.router)
app.include_router(policies.router)
app.include_router(notificaciones.router)
app.include_router(actividad.router)

# Root
@app.get("/")
async def root():
    return {"message": "Welcome to TaskKey API"}
