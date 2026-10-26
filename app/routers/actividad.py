"""Datos del hijo calculados a partir de actividad persistida, nunca ejemplos."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.utils.dependencies import get_current_child
from app.routers.tareas import obtener_mi_progreso
from app.schemas.hijos import HijoResponse

router = APIRouter(prefix='/actividad', tags=['actividad'])
AVATARES = [
    {'id': 'capicons', 'nombre': 'Capi clásico'},
    {'id': 'capifer', 'nombre': 'Capi explorador'},
    {'id': 'capiangel', 'nombre': 'Capi aventurero'},
    {'id': 'capihijo', 'nombre': 'Capi alegre'},
]


@router.get('/mi-resumen')
def resumen(conn=Depends(get_db), child=Depends(get_current_child)):
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM children WHERE id = %s', (child['id'],))
        perfil = cur.fetchone()
        if not perfil:
            raise HTTPException(404, 'Hijo no encontrado')
        cur.execute('SELECT * FROM device_policies WHERE child_id = %s', (child['id'],))
        politica = cur.fetchone()
    progreso = obtener_mi_progreso(conn=conn, current_child=child)
    return {'perfil': HijoResponse(**perfil), 'politica': politica, 'progreso': progreso}


@router.get('/mis-recompensas')
def recompensas(conn=Depends(get_db), child=Depends(get_current_child)):
    with conn.cursor() as cur:
        cur.execute('SELECT llaves_disponibles FROM children WHERE id = %s', (child['id'],))
        perfil = cur.fetchone()
        if not perfil:
            raise HTTPException(404, 'Hijo no encontrado')
        cur.execute('SELECT available_screen_time_minutes FROM device_policies WHERE child_id = %s', (child['id'],))
        politica = cur.fetchone()
        cur.execute('''SELECT ta.id, t.title, ta.completed_at,
            COALESCE(ta.earned_keys, t.reward_keys, 0) AS keys,
            COALESCE(ta.earned_minutes, COALESCE(t.duration_hours, 0) * 60 + COALESCE(t.duration_minutes, 0)) AS minutes
            FROM task_assignments ta JOIN tasks t ON t.id = ta.task_id
            WHERE ta.child_id = %s AND ta.status = 'verified'
            ORDER BY ta.completed_at DESC''', (child['id'],))
        historial = cur.fetchall()
    return {'llaves': perfil['llaves_disponibles'],
            'minutos': politica['available_screen_time_minutes'] if politica else 0,
            'historial': historial}


@router.get('/mis-logros')
def logros(conn=Depends(get_db), child=Depends(get_current_child)):
    progreso = obtener_mi_progreso(conn=conn, current_child=child)
    reglas = [
        ('primera', 'Primera misión', 'Completa una misión y consigue la aprobación de tu padre.', 'capicons', progreso.total_completadas, 1),
        ('diez', 'Diez misiones', 'Consigue diez misiones aprobadas.', 'capifer', progreso.total_completadas, 10),
        ('racha', 'Constancia', 'Consigue una racha de tres días con misiones aprobadas.', 'capiangel', progreso.racha_mas_larga, 3),
    ]
    return [{'id': id_, 'title': title, 'description': description, 'avatar_id': avatar,
             'actual': min(actual, objetivo), 'objetivo': objetivo, 'obtenido': actual >= objetivo}
            for id_, title, description, avatar, actual, objetivo in reglas]


@router.get('/mi-progreso-mensual')
def mensual(conn=Depends(get_db), child=Depends(get_current_child)):
    now = datetime.now(timezone.utc)
    # Tres meses de asignaciones; cumplimiento = verificadas / asignadas en ese mes.
    months = []
    for offset in (2, 1, 0):
        index = now.year * 12 + now.month - 1 - offset
        year, month = divmod(index, 12)
        months.append(f'{year:04d}-{month + 1:02d}')
    with conn.cursor() as cur:
        cur.execute('''SELECT to_char(assigned_at AT TIME ZONE 'UTC', 'YYYY-MM') AS mes,
            COUNT(*) AS asignadas, COUNT(*) FILTER (WHERE status = 'verified') AS completadas
            FROM task_assignments WHERE child_id = %s AND assigned_at >= %s
            GROUP BY mes ORDER BY mes''', (child['id'], months[0] + '-01T00:00:00+00:00'))
        rows = {row['mes']: row for row in cur.fetchall()}
    return [{'mes': month, 'asignadas': rows.get(month, {}).get('asignadas', 0),
             'completadas': rows.get(month, {}).get('completadas', 0),
             'cumplimiento': round(rows[month]['completadas'] * 100 / rows[month]['asignadas'], 1) if month in rows and rows[month]['asignadas'] else 0}
            for month in months]


@router.get('/avatares')
def avatares(child=Depends(get_current_child)):
    return AVATARES


class AvatarUpdate(BaseModel):
    avatar_id: str


@router.put('/mi-avatar', response_model=HijoResponse)
def guardar_avatar(data: AvatarUpdate, conn=Depends(get_db), child=Depends(get_current_child)):
    if data.avatar_id not in {item['id'] for item in AVATARES}:
        raise HTTPException(400, 'Avatar no disponible')
    with conn.cursor() as cur:
        cur.execute('UPDATE children SET avatar_id = %s WHERE id = %s RETURNING *', (data.avatar_id, child['id']))
        perfil = cur.fetchone()
    if not perfil:
        raise HTTPException(404, 'Hijo no encontrado')
    conn.commit()
    return perfil
