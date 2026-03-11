from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_padres

app = FastAPI(
    title="TaskKey API",
    version="0.1.0",
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

# Root
@app.get("/")
async def root():
    return {"message": "Welcome to TaskKey API"}