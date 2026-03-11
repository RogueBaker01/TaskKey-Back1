from passlib.context import CryptContext
#Library to encode and decode jwt tokens
from jose import jwt
from app.config import settings
from datetime import datetime, timedelta, timezone

#Configuracion de la contraseña
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#Funciones de autenticacion de Padres

#Funcion para hashear la contraseña
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

#Funcion para verificar la contraseña
def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

#Funcion para generar el token
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

#Decodificar y verificar el token
def verify_token(token: str) -> dict|None:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload