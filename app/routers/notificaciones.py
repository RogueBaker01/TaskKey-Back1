from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.schemas.notificaciones import DeviceTokenCreate, NotificacionResponse, MarcarLeidasRequest
from app.services.notifications import registrar_device_token, obtener_historial_notificaciones, marcar_como_leidas
from app.utils.dependencies import get_current_user

router = APIRouter(
    prefix="/api/notificaciones",
    tags=["Notificaciones"]
)

@router.post("/token", status_code=status.HTTP_201_CREATED)
def registrar_token(
    payload: DeviceTokenCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = UUID(current_user["sub"]) # El UUID del usuario actual desde JWT
    try:
        registrar_device_token(user_id, payload.token, payload.plataforma)
        return {"msg": "Token registrado exitosamente"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registrando token: {str(e)}"
        )

@router.get("", response_model=List[NotificacionResponse])
def get_notificaciones(
    current_user: dict = Depends(get_current_user)
):
    user_id = UUID(current_user["sub"])
    try:
        data = obtener_historial_notificaciones(user_id)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo notas: {str(e)}"
        )

@router.put("/leidas", status_code=status.HTTP_200_OK)
def marcar_leidas(
    payload: MarcarLeidasRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        marcar_como_leidas(payload.notificacion_ids)
        return {"msg": "Notificaciones actualizadas a leídas"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando notificaciones: {str(e)}"
        )
