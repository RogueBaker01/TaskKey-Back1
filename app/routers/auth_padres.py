from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.padres import PadresRegister, PadresLogin, PadresResponse, PadresConHijosResponse, PadresUpdate, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.utils.dependencies import get_current_user
from datetime import datetime, timezone

#datetime en formato utc para generalizarlo en cualquier zona horaria la app lo cambia a su formato local
router = APIRouter(prefix="/auth_padres", tags=["autenticacion"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
#Funcion para registrar padres usando el esquema PadresRegister y devuelve el token de autenticacion
async def register(padres: PadresRegister, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM padres WHERE email = %s", (padres.email,))
    if cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(padres.password)
    cursor.execute(
        "INSERT INTO padres (nombre, apellido, email, password_hash, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
        (padres.nombre, padres.apellido, padres.email, hashed_password, datetime.now(timezone.utc), datetime.now(timezone.utc))
    )
    new_padre = cursor.fetchone()
    conn.commit()
    cursor.close()

    #Crea el token
    token = create_access_token(data={"sub": str(new_padre["id"]), "email": new_padre["email"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "padre": new_padre, 
    }

@router.post("/login", response_model=TokenResponse)
#Funcion para iniciar sesion de padres usando el esquema PadresLogin y devuelve el token de autenticacion
async def login(padres: PadresLogin, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM padres WHERE email = %s", (padres.email,))
    padre = cursor.fetchone()
    cursor.close()

    if not padre:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrecto")

    if not verify_password(padres.password, padre["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrecto")
    
    #crea el token de autenticacion
    token = create_access_token(data={"sub": str(padre["id"]), "email": padre["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "padre": {
            "id": padre["id"],
            "nombre": padre["nombre"],
            "apellido": padre["apellido"],
            "email": padre["email"],
            "created_at": padre["created_at"],
            "updated_at": padre["updated_at"]
        },
    }

@router.get("/me", response_model=PadresConHijosResponse)
#Obtener el perfil del padre autenticado con sus hijos
def get_me_padre(conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, apellido, email, created_at, updated_at FROM padres WHERE id = %s",
        (current_user["id"],),
    )
    user = cursor.fetchone()

    if not user:
        cursor.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Padre no encontrado")
    
    # Obtener los hijos del padre (columnas reales de la tabla children)
    cursor.execute(
        "SELECT id, nombre, apellido, fecha_nacimiento FROM children WHERE parent_id = %s",
        (current_user["id"],),
    )
    hijos = cursor.fetchall()
    cursor.close()

    return {
        "id": user["id"],
        "nombre": user["nombre"],
        "apellido": user["apellido"],
        "email": user["email"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
        "hijos": hijos if hijos else []
    }

@router.put("/me", response_model=PadresResponse)
#Actualizar el perfil del padre autenticado (nombre y/o apellido)
def update_me_padre(data: PadresUpdate, conn=Depends(get_db), current_user: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    
    # Construir la query dinámicamente solo con campos enviados
    fields = []
    values = []
    
    if data.nombre is not None:
        fields.append("nombre = %s")
        values.append(data.nombre)
    if data.apellido is not None:
        fields.append("apellido = %s")
        values.append(data.apellido)
    
    if not fields:
        cursor.close()
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
    
    fields.append("updated_at = %s")
    values.append(datetime.now(timezone.utc))
    values.append(current_user["id"])
    
    query = f"UPDATE padres SET {', '.join(fields)} WHERE id = %s RETURNING *"
    cursor.execute(query, tuple(values))
    updated_padre = cursor.fetchone()
    conn.commit()
    cursor.close()
    
    if not updated_padre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Padre no encontrado")
    
    return updated_padre