from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.padres import PadresRegister, PadresLogin, PadresResponse, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token
from app.database import get_db

router = APIRouter(prefix = "/api/auth", tags=["autenticacion"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
#Funcion para registrar padres usando el esquema PadresRegister y devuelve el token de autenticacion
async def register(padres: PadresRegister, conn=Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM padres WHERE email = %s", (padres.email,))
    if cursor.fetchone():
        cursor.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(padres.password)
    cursor.execute("INSERT INTO padres (nombre, apellido, email, password) VALUES (%s, %s, %s, %s)", (padres.nombre, padres.apellido, padres.email, hashed_password))
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Correo o contraseña incorrecto")

    if not verify_password(padres.password, padre["password_hash"]):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrecto")
    #crea el token de autenticacion
    token = create_access_token(data={"sub": str(padre["id"]), "email": padre["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "padre": {
            "id": padre["id "],
            "nombre": padre["nombre"],
            "apellido": padre["apellido"],
            "email": padre["email"],
            "created_at": padre["created_at"],
            "updated_at": padre["updated_at"]
        },
    }

@router.get("me_padre", response_model=UserResponse)
def get_me_padre(conn=Depends(get_db), current_padre: dict = Depends(get_current_user)):
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, apellido, email, created_at FROM padres WHERE id = %s",
        (current_user["id"],),
    )
    user = cursor.fetchone()
    cursor.close

    if not padre:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, (current_user["id"],),)
    
    return {
        "id": user["id"],
        "nombre": user["nombre"],
        "apellido": user["apellido"],
        "email": user["email"]
    }