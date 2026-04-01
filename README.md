<h1 align="center">TaskKey — Backend</h1>

<p align="center">
  <strong>API REST para la plataforma de control parental TaskKey</strong><br/>
  Autenticación, gestión de tareas, recompensas y perfiles de padres e hijos.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/PostgreSQL-Azure-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Auth-JWT%20%7C%20bcrypt-orange" alt="Auth" />
  <a href="https://github.com/gallardoo8/Taskey-master"><img src="https://img.shields.io/badge/Frontend-Expo%20%7C%20React%20Native-61DAFB?logo=react" alt="Frontend" /></a>
  <img src="https://img.shields.io/badge/Estado-🚧%20En%20Construcción-yellow" alt="WIP" />
</p>

> **Proyecto en construcción** — Este backend se encuentra en desarrollo activo. Algunas funcionalidades pueden estar incompletas o sujetas a cambios.

---

## Descripción

API REST construida con **FastAPI** que sirve como backend de la aplicación móvil [Taskey](https://github.com/gallardoo8/Taskey-master). Gestiona la autenticación de padres e hijos, la creación y asignación de tareas, recompensas y perfiles familiares.

La base de datos es **PostgreSQL**, hospedada en **Azure Database for PostgreSQL**.

---

## Arquitectura

El proyecto sigue una arquitectura por capas:

```
Request (HTTP)
  └─► Router          ← define endpoints y valida entrada
        └─► Service       ← lógica de negocio (en desarrollo)
              └─► Database    ← conexión directa a PostgreSQL (psycopg2)
```

### Estructura del proyecto

```
TaskKey-Back1/
├── app/
│   ├── main.py             # Punto de entrada FastAPI, CORS, routers
│   ├── config.py           # Configuración con pydantic-settings (.env)
│   ├── database.py         # Conexión a PostgreSQL (psycopg2)
│   ├── routers/            # Endpoints agrupados por dominio
│   │   └── auth_padres.py  #   └─ Registro, login, perfil del padre
│   ├── schemas/            # Esquemas Pydantic (request/response)
│   │   └── padres.py       #   └─ PadresRegister, PadresLogin, TokenResponse
│   ├── services/           # Lógica de negocio (en desarrollo)
│   ├── models/             # Modelos de dominio (en desarrollo)
│   └── utils/
│       ├── security.py     # Hash, verificación de contraseña, JWT
│       └── dependencies.py # Dependencias de autenticación (OAuth2)
├── requirements.txt        # Dependencias de Python
├── .env                    # Variables de entorno (no versionado)
└── .gitignore
```

---

## Endpoints

### Autenticación de Padres (`/auth_padres`)

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| `POST` | `/auth_padres/register` | Registrar un nuevo padre | No |
| `POST` | `/auth_padres/login` | Iniciar sesión | No |
| `GET` | `/auth_padres/me` | Obtener perfil del padre con sus hijos | Bearer Token |

> Documentación interactiva disponible en `/docs` (Swagger UI) o `/redoc` cuando el servidor está corriendo.

---

## Tecnologías

| Categoría | Tecnología |
|---|---|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) |
| **Lenguaje** | Python 3.11+ |
| **Base de datos** | [PostgreSQL](https://www.postgresql.org/) (Azure) |
| **Driver DB** | [psycopg2](https://www.psycopg.org/) |
| **Autenticación** | JWT ([python-jose](https://python-jose.readthedocs.io/)) + [bcrypt](https://passlib.readthedocs.io/) |
| **Validación** | [Pydantic](https://docs.pydantic.dev/) v2 |
| **Configuración** | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) + dotenv |
| **Servidor** | [Uvicorn](https://www.uvicorn.org/) |

---

## Requisitos Previos

- [Python](https://www.python.org/downloads/) 3.11+
- [Git](https://git-scm.com/)
- Acceso a una instancia de PostgreSQL (local o Azure)

---

## Instalación y Configuración

```bash
# 1. Clonar el repositorio
git clone https://github.com/RogueBaker01/TaskKey-Back1
cd TaskKey-Back1

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Configurar variables de entorno (ver sección siguiente)
cp .env.example .env

# 6. Iniciar el servidor
uvicorn app.main:app --reload
```

El servidor estará disponible en `http://localhost:8000`.

---

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Conexión a PostgreSQL
DB_ENDPOINT=tu-servidor.postgres.database.azure.com
DB_NAME=taskkey
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_PORT=5432

# JWT
SECRET_KEY=tu_clave_secreta_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## Repositorios Relacionados

| Repositorio | Descripción | Stack |
|---|---|---|
| **[Taskey-master](https://github.com/gallardoo8/Taskey-master)** | App móvil (frontend) | Expo · React Native · TypeScript |
| **[TaskKey-Back1](https://github.com/RogueBaker01/TaskKey-Back1)** | API REST (este repo) | FastAPI · PostgreSQL · Azure |

---

## Equipo

| Nombre | Rol |
|---|---|
| Gabriela Pacheco Sanchez | Project Manager |
| Constanza Lanuza Gallardo | Frontend Developer |
| Bernardo David Nolasco Vargas | Backend Developer |
| Diego Fernando Ramírez García | Backend Developer |
| Guadalupe Álvarez Bazaldúa | Designer |
| Mariana Araujo Flores | Designer |
| Angélica Cenobio Arreola | Frontend Developer |

---

## Licencia

Este proyecto es privado y de uso exclusivo del equipo de desarrollo de Taskey.