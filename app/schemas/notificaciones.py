from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from uuid import UUID
from datetime import datetime

class DeviceTokenCreate(BaseModel):
    token: str
    plataforma: Literal['android', 'ios', 'expo']

class NotificacionBase(BaseModel):
    tipo: Literal['TAREA_COMPLETADA', 'TIEMPO_LIMITE', 'TAREA_FALLIDA', 'META_SEMANAL', 'TAREA_CONFIRMADA']
    titulo: str
    mensaje: str
    data_extra: Optional[Dict[str, Any]] = None

class NotificacionCreate(NotificacionBase):
    usuario_id: UUID

class NotificacionResponse(NotificacionBase):
    id: UUID
    usuario_id: UUID
    leida: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class MarcarLeidasRequest(BaseModel):
    notificacion_ids: list[UUID]

class NotificacionTestRequest(BaseModel):
    tipo: Literal['TAREA_COMPLETADA', 'TIEMPO_LIMITE', 'TAREA_FALLIDA', 'META_SEMANAL', 'TAREA_CONFIRMADA'] = 'TAREA_COMPLETADA'
    titulo: str = "Notificación de prueba"
    mensaje: str = "Esta es una notificación de prueba enviada desde el backend."
    data_extra: Optional[Dict[str, Any]] = None
