from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.hijos import HijoCreate, HijoUpdate, HijoResponse, HijoDetailResponse, CodigoVinculacionResponse
from app.database import get_db
from app.utils.dependencies import get_current_user
from datetime import datetime, timezone, timedelta
import secrets
from app.utils.security import hash_password

router = APIRouter(prefix="/hijos", tags=["hijos"])


@router.post("/", response_model=HijoDetailResponse, status_code=status.HTTP_201_CREATED)
def crear_hijo(hijo: HijoCreate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()

    # Generar codigo de vinculacion aleatorio (10 caracteres)
    codigo_plano = secrets.token_urlsafe(7)[:10]
    codigo_hash = hash_password(codigo_plano)
    expira_en = datetime.now(timezone.utc) + timedelta(hours=24)

    cursor.execute(
        "INSERT INTO children (parent_id, nombre, apellido, genero, fecha_nacimiento, codigo_auth_hash, code_expires_at, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *",
        (current_user["id"], hijo.nombre, hijo.apellido, hijo.genero, hijo.fecha_nacimiento, codigo_hash, expira_en, datetime.now(timezone.utc))
    )
    new_hijo = cursor.fetchone()
    conn.commit()
    cursor.close()

    return {
        **new_hijo,
        "estado_vinculacion": "pendiente",
        "codigo_vinculacion": codigo_plano,
    }


@router.get("/", response_model=list[HijoDetailResponse])
def listar_hijos(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM children WHERE parent_id = %s ORDER BY created_at ASC",
        (current_user["id"],)
    )
    hijos = cursor.fetchall()
    cursor.close()

    resultado = []
    for hijo in hijos:
        # Determinar estado de vinculacion: si no tiene codigo o ya expiro → vinculado
        tiene_codigo = hijo.get("codigo_auth_hash") is not None
        code_expirado = False
        if hijo.get("code_expires_at"):
            # Comparar sin timezone si la BD no guarda con tz
            code_expirado = hijo["code_expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
        
        # Si tiene codigo activo (no expirado) → pendiente; si no tiene o expiró → vinculado
        estado = "pendiente" if (tiene_codigo and not code_expirado) else "vinculado"
        
        resultado.append({
            **hijo,
            "estado_vinculacion": estado,
            "codigo_vinculacion": None,  # No mostramos el codigo en el listado
        })

    return resultado


@router.get("/{hijo_id}", response_model=HijoDetailResponse)
def obtener_hijo(hijo_id: str, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM children WHERE id = %s AND parent_id = %s",
        (hijo_id, current_user["id"])
    )
    hijo = cursor.fetchone()
    cursor.close()

    if not hijo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hijo no encontrado")

    tiene_codigo = hijo.get("codigo_auth_hash") is not None
    code_expirado = False
    if hijo.get("code_expires_at"):
        code_expirado = hijo["code_expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    estado = "pendiente" if (tiene_codigo and not code_expirado) else "vinculado"

    return {
        **hijo,
        "estado_vinculacion": estado,
        "codigo_vinculacion": None,
    }


@router.put("/{hijo_id}", response_model=HijoResponse)
def editar_hijo(hijo_id: str, data: HijoUpdate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()

    # Verificar que el hijo pertenece al padre
    cursor.execute(
        "SELECT id FROM children WHERE id = %s AND parent_id = %s",
        (hijo_id, current_user["id"])
    )
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hijo no encontrado")

    # Construir query dinamica con solo los campos enviados
    fields = []
    values = []

    if data.nombre is not None:
        fields.append("nombre = %s")
        values.append(data.nombre)
    if data.apellido is not None:
        fields.append("apellido = %s")
        values.append(data.apellido)
    if data.genero is not None:
        fields.append("genero = %s")
        values.append(data.genero)
    if data.fecha_nacimiento is not None:
        fields.append("fecha_nacimiento = %s")
        values.append(data.fecha_nacimiento)

    if not fields:
        cursor.close()
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    values.append(hijo_id)
    values.append(current_user["id"])

    query = f"UPDATE children SET {', '.join(fields)} WHERE id = %s AND parent_id = %s RETURNING *"
    cursor.execute(query, tuple(values))
    updated_hijo = cursor.fetchone()
    conn.commit()
    cursor.close()

    if not updated_hijo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hijo no encontrado")

    return updated_hijo


@router.delete("/{hijo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_hijo(hijo_id: str, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM children WHERE id = %s AND parent_id = %s RETURNING id",
        (hijo_id, current_user["id"])
    )
    deleted = cursor.fetchone()
    conn.commit()
    cursor.close()

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hijo no encontrado")

    return None


@router.post("/{hijo_id}/codigo", response_model=CodigoVinculacionResponse)
def generar_codigo(hijo_id: str, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()

    # Verificar que el hijo pertenece al padre
    cursor.execute(
        "SELECT id FROM children WHERE id = %s AND parent_id = %s",
        (hijo_id, current_user["id"])
    )
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hijo no encontrado")

    # Generar nuevo codigo
    codigo_plano = secrets.token_urlsafe(7)[:10]
    codigo_hash = hash_password(codigo_plano)
    expira_en = datetime.now(timezone.utc) + timedelta(hours=24)

    cursor.execute(
        "UPDATE children SET codigo_auth_hash = %s, code_expires_at = %s WHERE id = %s AND parent_id = %s",
        (codigo_hash, expira_en, hijo_id, current_user["id"])
    )
    conn.commit()
    cursor.close()

    return {
        "hijo_id": hijo_id,
        "codigo": codigo_plano,
        "expira_en": expira_en,
        "mensaje": f"Código generado. Expira en 24 horas.",
    }
