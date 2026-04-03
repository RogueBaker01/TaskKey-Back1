from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

# Esquema para crear un hijo
class HijoCreate(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    genero: Optional[str] = None 
    fecha_nacimiento: Optional[date] = None

# Esquema para actualizar un hijo
class HijoUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    genero: Optional[str] = None
    fecha_nacimiento: Optional[date] = None

# Esquema de respuesta basica de un hijo
class HijoResponse(BaseModel):
    id: UUID
    parent_id: UUID
    nombre: str
    apellido: Optional[str] = None
    genero: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Esquema de respuesta con detalle de vinculacion
class HijoDetailResponse(HijoResponse):
    estado_vinculacion: str  # "vinculado" | "pendiente"
    codigo_vinculacion: Optional[str] = None  # Solo se muestra si estado es "pendiente"

# Esquema de respuesta del codigo de vinculacion
class CodigoVinculacionResponse(BaseModel):
    hijo_id: UUID
    codigo: str
    expira_en: datetime
    mensaje: str
