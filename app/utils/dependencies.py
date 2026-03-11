from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.security import verify_token

#Esquema de autenticacion
oauth2_scheme_padre = OAuth2PasswordBearer(tokenUrl="/api/auth_padres/login")
oauth2_scheme_hijo = OAuth2PasswordBearer(tokenUrl="")


def get_current_user(token: str = Depends(oauth2_scheme_padre)) -> dict:
    
    #Verfica el token regresa 401 si es no es valido
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    #Verifica que el token tenga un sub (id del usuario)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"id": user_id, "email": payload.get("email", "")}

def get_current_child(token: str = Depends(oauth2_scheme_hijo)) -> dict:
    
    #Verfica el token regresa 401 si es no es valido
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    #Verifica que el token tenga un sub (id del usuario)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"id": user_id, "role": "child"}
