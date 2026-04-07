from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional, List

#Esquemas para tareas
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    reward_keys: Optional[int] = 0         
    duration_hours: Optional[int] = 0      
    duration_minutes: Optional[int] = 0    

#Esquema para actualizar tareas
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    reward_keys: Optional[int] = None
    duration_hours: Optional[int] = None
    duration_minutes: Optional[int] = None

#Esquema de respuesta de tareas
class TaskResponse(BaseModel):
    id: UUID
    parent_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    reward_keys: Optional[int] = None
    duration_hours: Optional[int] = None
    duration_minutes: Optional[int] = None
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

#Esquema de respuesta de asignaciones
class TaskAssignmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    child_id: UUID
    status: str
    assigned_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

#Esquema de respuesta de tareas con asignaciones
class TaskWithAssignmentsResponse(TaskResponse):
    assignments: List[TaskAssignmentResponse] = []
