from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.hijos import HijoLogin, HijoResponse, HijoTokenResponse
from app.utils.security import verify_password, create_access_token
from app.database import get_db
from app.utils.dependencies import get_current_child
from datetime import datetime, timezone
from app.utils.limiter import limiter

router = APIRouter(prefix="/auth_hijos", tags=["autenticacion_hijos"])


@router.post("/login", response_model=HijoTokenResponse)
@limiter.limit("5/minute")
# Funcion para que el hijo vincule su dispositivo usando el codigo generado por el padre
async def login(request: Request, data: HijoLogin, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM children WHERE codigo_auth_hash IS NOT NULL AND code_expires_at > %s",
        (datetime.now(timezone.utc),)
    )
    candidatos = cursor.fetchall()

    hijo = next(
        (c for c in candidatos if verify_password(data.codigo, c["codigo_auth_hash"])),
        None,
    )

    if not hijo:
        cursor.close()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Código inválido o expirado")

    # El codigo es de un solo uso: se invalida una vez vinculado el dispositivo
    cursor.execute(
        "UPDATE children SET codigo_auth_hash = NULL, code_expires_at = NULL WHERE id = %s",
        (hijo["id"],)
    )
    conn.commit()
    cursor.close()

    token = create_access_token(data={"sub": str(hijo["id"]), "role": "child"})

    return {
        "access_token": token,
        "token_type": "bearer",
        "child": hijo,
    }


@router.get("/me", response_model=HijoResponse)
# Obtener el perfil del hijo autenticado
def get_me_hijo(conn=Depends(get_db), current_child: dict = Depends(get_current_child)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM children WHERE id = %s", (current_child["id"],))
    hijo = cursor.fetchone()
    cursor.close()

    if not hijo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hijo no encontrado")

    return hijo
