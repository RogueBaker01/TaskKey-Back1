from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_padres, hijos, tareas

app = FastAPI(
    title="TaskKey API",
    version="1.0.0",
    description="Backend API for TaskKey",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#routers
app.include_router(auth_padres.router)
app.include_router(hijos.router)
app.include_router(tareas.router)

# Root
@app.get("/")
async def root():
    return {"message": "Welcome to TaskKey API"}