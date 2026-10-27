from uuid import UUID
from pydantic import BaseModel, Field
from datetime import time, datetime
from typing import Optional, Any

# Esquema para actualizar la política
class DevicePolicyUpdate(BaseModel):
    available_screen_time_minutes: Optional[int] = Field(default=None, ge=0)
    sleep_start_time: Optional[time] = None
    sleep_end_time: Optional[time] = None
    sleep_days: Optional[str] = None
    restricted_apps: list[str] = Field(default_factory=list)
    sleep_enabled: bool = True

# Esquema de respuesta de política
class DevicePolicyResponse(BaseModel):
    sleep_enabled: bool = True
    id: UUID
    child_id: UUID
    available_screen_time_minutes: int
    sleep_start_time: time
    sleep_end_time: time
    sleep_days: str
    restricted_apps: Any
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
