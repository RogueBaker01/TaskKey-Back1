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

    return {"id": user_id, "role": "child"}
