from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_padres, hijos, tareas, policies
from app.config import settings
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.utils.limiter import limiter

app = FastAPI(
    title="TaskKey API",
    version="1.0.0",
    description="Backend API for TaskKey",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(',')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#routers
app.include_router(auth_padres.router)
app.include_router(hijos.router)
app.include_router(tareas.router)
app.include_router(policies.router)

# Root
@app.get("/")
async def root():
    return {"message": "Welcome to TaskKey API"}
