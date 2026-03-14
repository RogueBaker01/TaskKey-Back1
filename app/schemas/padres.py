from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

#Esquema de registro de padres
class PadresRegister(BaseModel):
    nombre: str
    apellido: str
    email: str
    password: str

#Esquema de login de padres
class PadresLogin(BaseModel):
    email: str
    password: str

#Esquema de respuesta de un hijo
class HijoResponse(BaseModel):
    id: UUID
    nombre: str
    apellido: str
    fecha_nacimiento: Optional[date] = None

    class Config:
        from_attributes = True

#Esquema de respuesta de padres
class PadresResponse(BaseModel):
    id: UUID
    nombre: str
    apellido: str
    email: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

#Esquema de respuesta de padres con hijos (para /me)
class PadresConHijosResponse(PadresResponse):
    hijos: List[HijoResponse] = []

#Esquema de respuesta de tokens
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    padre: PadresResponse
