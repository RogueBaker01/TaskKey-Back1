from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor
import json
from uuid import UUID

from app.database import get_db, get_connection
from app.utils.dependencies import get_current_user
from app.schemas.policies import DevicePolicyResponse, DevicePolicyUpdate

router = APIRouter(
    prefix="/policies",
    tags=["Policies"]
)

@router.get("/{child_id}", response_model=DevicePolicyResponse)
def get_device_policy(child_id: UUID, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verificar propiedad del hijo
            cur.execute("SELECT id FROM children WHERE id = %s AND parent_id = %s", (str(child_id), str(current_user["id"])))
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
            
            return policy
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.put("/{child_id}", response_model=DevicePolicyResponse)
def update_device_policy(child_id: UUID, payload: DevicePolicyUpdate, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM children WHERE id = %s AND parent_id = %s", (str(child_id), str(current_user["id"])))
            if not cur.fetchone():
                raise HTTPException(status_code=403, detail="No tienes acceso a editar este hijo")

            update_data = payload.model_dump(exclude_unset=True)
            if not update_data:
                raise HTTPException(status_code=400, detail="No se proveyeron datos para actualizar")

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
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
