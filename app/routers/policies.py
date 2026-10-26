from fastapi import APIRouter, Depends, HTTPException
from psycopg2.extras import RealDictCursor
import json
from uuid import UUID

from app.database import get_db
from app.services.policies import ensure_device_policy
import logging

logger = logging.getLogger(__name__)
from app.utils.dependencies import get_current_user
from app.schemas.policies import DevicePolicyResponse, DevicePolicyUpdate

router = APIRouter(
    prefix="/policies",
    tags=["Policies"]
)

APP_CATALOG = [
    {'id': '1', 'name': 'YouTube', 'category': 'Entretenimiento'},
    {'id': '2', 'name': 'Netflix', 'category': 'Entretenimiento'},
    {'id': '3', 'name': 'TikTok', 'category': 'Entretenimiento'},
    {'id': '4', 'name': 'Disney+', 'category': 'Entretenimiento'},
    {'id': '5', 'name': 'HBO Max', 'category': 'Entretenimiento'},
    {'id': '6', 'name': 'Instagram', 'category': 'Redes sociales'},
    {'id': '7', 'name': 'Facebook', 'category': 'Redes sociales'},
    {'id': '8', 'name': 'Roblox', 'category': 'Juegos'},
    {'id': '9', 'name': 'Subway Surfers', 'category': 'Juegos'},
    {'id': '10', 'name': 'Geometry Dash', 'category': 'Juegos'},
]

@router.get('/catalogo/apps')
def catalogo_apps(current_user: dict = Depends(get_current_user)):
    return APP_CATALOG


@router.get("/{child_id}", response_model=DevicePolicyResponse)
def get_device_policy(child_id: UUID, current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verificar propiedad del hijo
            cur.execute("SELECT id FROM children WHERE id = %s AND parent_id = %s FOR UPDATE", (str(child_id), str(current_user["id"])))
            if not cur.fetchone():
                raise HTTPException(status_code=403, detail="No tienes acceso a este hijo")

            cur.execute("SELECT * FROM device_policies WHERE child_id = %s", (str(child_id),))
            policy = cur.fetchone()
            if not policy:
                # Para hijos que se crearon antes de tener las policies, hacer lazy-creation
                cur.execute(
                    "INSERT INTO device_policies (child_id, available_screen_time_minutes, sleep_start_time, sleep_end_time, sleep_days, restricted_apps, created_at, updated_at) VALUES (%s, 0, '21:30:00', '07:30:00', 'Lun,Mar,Mie,Jue,Vie,Sab,Dom', '[]', NOW(), NOW()) RETURNING *",
                    (str(child_id),)
                )
                policy = cur.fetchone()
            
            conn.commit()
            return policy
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        logger.exception("No se pudo consultar la política")
        raise HTTPException(status_code=500, detail="No se pudo consultar la política")

@router.put("/{child_id}", response_model=DevicePolicyResponse)
def update_device_policy(child_id: UUID, payload: DevicePolicyUpdate, current_user: dict = Depends(get_current_user), conn=Depends(get_db)):
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM children WHERE id = %s AND parent_id = %s FOR UPDATE", (str(child_id), str(current_user["id"])))
            if not cur.fetchone():
                raise HTTPException(status_code=403, detail="No tienes acceso a editar este hijo")

            update_data = payload.model_dump(exclude_unset=True)
            if not update_data:
                raise HTTPException(status_code=400, detail="No se proveyeron datos para actualizar")

            if 'restricted_apps' in update_data and not set(update_data['restricted_apps']).issubset({a['id'] for a in APP_CATALOG}):
                raise HTTPException(400, 'Aplicación no disponible en el catálogo')
            ensure_device_policy(cur, child_id)
            query_parts = []
            values = []
            for key, value in update_data.items():
                if key == "restricted_apps" and value is not None:
                    query_parts.append(f"{key} = %s::jsonb")
                    values.append(json.dumps(value))
                else:
                    query_parts.append(f"{key} = %s")
                    values.append(value)
            
            query_parts.append("updated_at = NOW()")
            values.append(str(child_id))

            query = f"UPDATE device_policies SET {', '.join(query_parts)} WHERE child_id = %s RETURNING *"
            
            cur.execute(query, tuple(values))
            updated_policy = cur.fetchone()
            if not updated_policy:
                raise HTTPException(status_code=404, detail="Politica no encontrada")
            conn.commit()
            return updated_policy

    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        logger.exception("No se pudo guardar la política")
        raise HTTPException(status_code=500, detail="No se pudo guardar la política")
