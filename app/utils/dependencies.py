from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import verify_token

# HTTPBearer muestra un campo simple "token" en Swagger UI en lugar del formulario OAuth2
http_bearer = HTTPBearer(auto_error=True)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> dict:
    
    # Verifica el token, regresa 401 si no es válido
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verifica que el token tenga un sub (id del usuario)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Los tokens de hijo no pueden usarse en rutas de padre
    if payload.get("role") == "child":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este token no tiene permisos de padre",
        )

    return {"id": user_id, "email": payload.get("email", "")}

def get_current_child(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> dict:
    
    # Verifica el token, regresa 401 si no es válido
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verifica que el token tenga un sub (id del usuario)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Solo tokens emitidos para hijos pueden usar rutas de hijo
    if payload.get("role") != "child":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este token no tiene permisos de hijo",
        )

    return {"id": user_id, "role": "child"}

def get_current_actor(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> dict:
    """ Para rutas compartidas (p.ej. notificaciones) a las que puede entrar tanto un padre como un hijo. """

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = "child" if payload.get("role") == "child" else "padre"
    return {"id": user_id, "role": role}
