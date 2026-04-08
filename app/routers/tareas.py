from fastapi import APIRouter, Depends, HTTPException, status
from app.services.notifications import enviar_notificacion
from app.schemas.tareas import TaskCreate, TaskUpdate, TaskResponse, TaskAssignmentCreate, TaskAssignmentUpdateStatus, TaskAssignmentResponse, TaskWithAssignmentsResponse
from app.database import get_db
from app.utils.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/tareas", tags=["tareas"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def crear_tarea(task: TaskCreate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    
    query = "INSERT INTO tasks (parent_id, title, description, due_date, due_time, reward_keys, duration_hours, duration_minutes, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *"
    values = (
        current_user["id"], task.title, task.description, 
        task.due_date, task.due_time, task.reward_keys, task.duration_hours, task.duration_minutes,
        datetime.now(timezone.utc), datetime.now(timezone.utc)
    )
    
    cursor.execute(query, values)
    new_task = cursor.fetchone()
    conn.commit()
    cursor.close()
    
    return new_task


@router.get("/", response_model=list[TaskWithAssignmentsResponse])
def listar_tareas(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    # Obtener todas las tareas del padre
    cursor.execute(
        "SELECT * FROM tasks WHERE parent_id = %s ORDER BY created_at DESC",
        (current_user["id"],)
    )
    tasks = cursor.fetchall()
    
    if not tasks:
        cursor.close()
        return []

    # Obtener las asignaciones para saber cada estado
    task_ids = tuple([t["id"] for t in tasks])
    cursor.execute(
        "SELECT * FROM task_assignments WHERE task_id IN %s",
        (task_ids,)
    )
    assignments = cursor.fetchall()
    cursor.close()

    # Agrupar las asignaciones a cada tarea
    resultado = []
    for t in tasks:
        task_data = dict(t)
        task_data["assignments"] = [a for a in assignments if a["task_id"] == t["id"]]
        resultado.append(task_data)
        
    return resultado


@router.get("/{task_id}", response_model=TaskWithAssignmentsResponse)
def obtener_tarea(task_id: str, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tasks WHERE id = %s AND parent_id = %s",
        (task_id, current_user["id"])
    )
    task = cursor.fetchone()
    
    if not task:
        cursor.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    cursor.execute("SELECT * FROM task_assignments WHERE task_id = %s", (task_id,))
    assignments = cursor.fetchall()
    cursor.close()

    return {**task, "assignments": assignments}


@router.put("/{task_id}", response_model=TaskResponse)
def actualizar_tarea(task_id: str, data: TaskUpdate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    
    # Validar propiedad
    cursor.execute("SELECT id FROM tasks WHERE id = %s AND parent_id = %s", (task_id, current_user["id"]))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

    fields = []
    values = []

    if data.title is not None:
        fields.append("title = %s")
        values.append(data.title)
    if data.description is not None:
        fields.append("description = %s")
        values.append(data.description)
    if data.due_date is not None:
        fields.append("due_date = %s")
        values.append(data.due_date)
    if data.due_time is not None:
        fields.append("due_time = %s")
        values.append(data.due_time)
    if data.reward_keys is not None:
        fields.append("reward_keys = %s")
        values.append(data.reward_keys)
    if data.duration_hours is not None:
        fields.append("duration_hours = %s")
        values.append(data.duration_hours)
    if data.duration_minutes is not None:
        fields.append("duration_minutes = %s")
        values.append(data.duration_minutes)

    if not fields:
        cursor.close()
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    fields.append("updated_at = %s")
    values.append(datetime.now(timezone.utc))
    values.append(task_id)

    query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = %s RETURNING *"
    cursor.execute(query, tuple(values))
    updated_task = cursor.fetchone()
    conn.commit()
    cursor.close()

    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tarea(task_id: str, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM tasks WHERE id = %s AND parent_id = %s RETURNING id",
        (task_id, current_user["id"])
    )
    deleted = cursor.fetchone()
    conn.commit()
    cursor.close()
    
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return None

@router.post("/{task_id}/asignar", response_model=TaskAssignmentResponse, status_code=status.HTTP_201_CREATED)
def asignar_tarea(task_id: str, data: TaskAssignmentCreate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    
    # Validar que la tarea es del padre
    cursor.execute("SELECT id FROM tasks WHERE id = %s AND parent_id = %s", (task_id, current_user["id"]))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
        
    # Validar que el hijo es del padre
    cursor.execute("SELECT id FROM children WHERE id = %s AND parent_id = %s", (str(data.child_id), current_user["id"]))
    if not cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El hijo no pertenece a tu cuenta")

    # Comprobar que no esté asignado ya
    cursor.execute("SELECT id FROM task_assignments WHERE task_id = %s AND child_id = %s", (task_id, str(data.child_id)))
    if cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La tarea ya fue asignada a este hijo")

    # Asignar
    cursor.execute(
        "INSERT INTO task_assignments (task_id, child_id, status, assigned_at) VALUES (%s, %s, %s, %s) RETURNING *",
        (task_id, str(data.child_id), "assigned", datetime.now(timezone.utc))
    )
    assignment = cursor.fetchone()
    conn.commit()
    cursor.close()

    return assignment


@router.put("/asignaciones/{assignment_id}/estado", response_model=TaskAssignmentResponse)
def cambiar_estado_asignacion(assignment_id: str, data: TaskAssignmentUpdateStatus, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    
    # Validar que la asignación existe y pertenece a una tarea del padre actual
    cursor.execute("SELECT ta.* FROM task_assignments ta JOIN tasks t ON ta.task_id = t.id WHERE ta.id = %s AND t.parent_id = %s", (assignment_id, current_user["id"]))
    
    assignment = cursor.fetchone()
    if not assignment:
        cursor.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación o Tarea no encontrada")

    estados_validos = ["assigned", "in_progress", "completed", "verified"]
    if data.status not in estados_validos:
        cursor.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estado inválido. Debe ser uno de {estados_validos}")

    completed_at = datetime.now(timezone.utc) if data.status in ["completed", "verified"] else None

    # Actualizar estado
    cursor.execute(
        "UPDATE task_assignments SET status = %s, completed_at = COALESCE(%s, completed_at) WHERE id = %s RETURNING *",
        (data.status, completed_at, assignment_id)
    )
    updated_assignment = cursor.fetchone()

    if data.status == "verified" and assignment["status"] != "verified":
        cursor.execute("SELECT duration_hours, duration_minutes FROM tasks WHERE id = %s", (assignment["task_id"],))
        task_info = cursor.fetchone()
        if task_info:
            minutos_ganados = (task_info.get("duration_hours") or 0) * 60 + (task_info.get("duration_minutes") or 0)
            if minutos_ganados > 0:
                cursor.execute(
                    "UPDATE device_policies SET available_screen_time_minutes = available_screen_time_minutes + %s, updated_at = NOW() WHERE child_id = %s",
                    (minutos_ganados, str(assignment["child_id"]))
                )

    conn.commit()
    cursor.close()

    return updated_assignment

@router.put("/asignaciones/{assignment_id}/estado/child", response_model=TaskAssignmentResponse)
def cambiar_estado_asignacion_hijo(assignment_id: str, data: TaskAssignmentUpdateStatus, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    """ Endpoint para que el HIJO marque su tarea como en progreso o completada. """
    cursor = conn.cursor()
    
    # Validar que la asignación existe y pertenece al hijo
    cursor.execute("SELECT ta.* FROM task_assignments ta WHERE ta.id = %s AND ta.child_id = %s", (assignment_id, current_user["id"]))
    assignment = cursor.fetchone()
    
    if not assignment:
        cursor.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada o no te pertenece")
        
    estados_hijo = ["assigned", "in_progress", "completed"]
    if data.status not in estados_hijo:
        cursor.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El hijo solo puede cambiar a: {estados_hijo}")

    completed_at = datetime.now(timezone.utc) if data.status == "completed" else None

    # Actualizar estado
    cursor.execute(
        "UPDATE task_assignments SET status = %s, completed_at = COALESCE(%s, completed_at) WHERE id = %s RETURNING *",
        (data.status, completed_at, assignment_id)
    )
    updated_assignment = cursor.fetchone()

    # == INICIO NOTIFICACION AL PADRE ==
    if data.status == "completed" and assignment["status"] != "completed":
        cursor.execute("SELECT parent_id FROM tasks WHERE id = %s", (assignment["task_id"],))
        task = cursor.fetchone()
        if task:
            try:
                enviar_notificacion(
                    usuario_id=task["parent_id"],
                    tipo="TAREA_COMPLETADA",
                    titulo="Tarea Completada",
                    mensaje="Tu hijo ha marcado una tarea como completada. Revisa la evidencia.",
                    data_extra={"assignment_id": str(assignment_id)}
                )
            except Exception as e:
                print(f"Error enviando notificacion: {e}")
    # == FIN NOTIFICACION ==

    conn.commit()
    cursor.close()
    return updated_assignment
