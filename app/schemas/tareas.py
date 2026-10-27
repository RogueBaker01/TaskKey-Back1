from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime, date, time
from typing import Optional, List

#Esquemas para tareas
class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    reward_keys: Optional[int] = Field(default=0, ge=0)
    duration_hours: Optional[int] = Field(default=0, ge=0)
    duration_minutes: Optional[int] = Field(default=0, ge=0)

#Esquema para actualizar tareas
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    reward_keys: Optional[int] = Field(default=None, ge=0)
    duration_hours: Optional[int] = Field(default=None, ge=0)
    duration_minutes: Optional[int] = Field(default=None, ge=0)

#Esquema de respuesta de tareas
class TaskResponse(BaseModel):
    id: UUID
    parent_id: UUID
    title: str
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    reward_keys: Optional[int] = Field(default=None, ge=0)
    duration_hours: Optional[int] = Field(default=None, ge=0)
    duration_minutes: Optional[int] = Field(default=None, ge=0)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

#Esquemas para asignaciones de tareas
class TaskAssignmentCreate(BaseModel):
    child_id: UUID

#Esquema para actualizar estado de asignaciones
class TaskAssignmentUpdateStatus(BaseModel):
    status: str
    evidencia_foto: Optional[str] = Field(default=None, max_length=4_000_000, pattern=r"^data:image/(jpeg|png);base64,[A-Za-z0-9+/=]+$")  # imagen en base64, solo la usa el hijo al marcar "completed"

#Esquema de respuesta de asignaciones
class TaskAssignmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    child_id: UUID
    status: str
    assigned_at: datetime
    completed_at: Optional[datetime] = None
    evidencia_foto: Optional[str] = None

    class Config:
        from_attributes = True

#Esquema de respuesta de tareas con asignaciones
class TaskWithAssignmentsResponse(TaskResponse):
    assignments: List[TaskAssignmentResponse] = []

#Esquema de respuesta del progreso/racha del hijo (calculado, no persistido)
class ProgresoResponse(BaseModel):
    total_completadas: int
    completadas_semana: int
    racha_actual: int
    racha_mas_larga: int
