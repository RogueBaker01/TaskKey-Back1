# Esquema real de la base de datos (inferido del código)

Este proyecto no tiene un ORM ni archivos de modelos (`app/models/` está vacío
a propósito). Todo el acceso a datos es SQL crudo con `psycopg2`. Esta tabla
se construyó grepeando **cada** `SELECT`/`INSERT`/`UPDATE` del código (no se
adivinó ningún nombre) para tener una referencia única contra la cual cruzar
tu base real de Azure antes de desplegar.

Las columnas marcadas **(nueva)** requieren correr `migrations/001_*.sql` y
`migrations/002_*.sql` — sin eso, cualquier endpoint que las use responde 500.

## `padres`
| Columna | Usada en |
|---|---|
| id | todos |
| nombre, apellido, email | auth_padres.py |
| password_hash | auth_padres.py |
| created_at, updated_at | auth_padres.py |

## `children`
| Columna | Usada en |
|---|---|
| id, parent_id | hijos.py, tareas.py, auth_hijos.py, policies.py, actividad.py |
| nombre, apellido, genero, fecha_nacimiento | hijos.py |
| codigo_auth_hash, code_expires_at | hijos.py, auth_hijos.py |
| created_at | hijos.py |
| **llaves_disponibles** (nueva, INTEGER DEFAULT 0) | tareas.py (se acredita al verificar), actividad.py |
| **avatar_id** (nueva, TEXT nullable) | auth_padres.py, hijos.py, actividad.py |

## `tasks`
| Columna | Usada en |
|---|---|
| id, parent_id | tareas.py |
| title, description, due_date, due_time | tareas.py |
| reward_keys, duration_hours, duration_minutes | tareas.py (se usan para acreditar llaves/minutos) |
| **color** (nueva, TEXT nullable, validado como `#RRGGBB` en el schema) | tareas.py |
| created_at, updated_at | tareas.py |

## `task_assignments`
| Columna | Usada en |
|---|---|
| id, task_id, child_id | tareas.py |
| status (`assigned`\|`in_progress`\|`completed`\|`verified`) | tareas.py |
| assigned_at, completed_at | tareas.py |
| **evidencia_foto** (nueva, TEXT nullable, base64) | tareas.py |
| **earned_keys**, **earned_minutes** (nuevas, INTEGER nullable) | tareas.py (snapshot de lo que se gano al verificar, para que no cambie si la tarea se edita despues) |

## `device_policies`
| Columna | Usada en |
|---|---|
| id, child_id | policies.py, hijos.py, tareas.py, actividad.py |
| available_screen_time_minutes | policies.py, tareas.py, actividad.py |
| sleep_start_time, sleep_end_time, sleep_days | policies.py |
| restricted_apps (JSONB) | policies.py |
| **sleep_enabled** (nueva, BOOLEAN DEFAULT TRUE) | policies.py |
| created_at, updated_at | policies.py |

## `device_tokens`
| Columna | Usada en |
|---|---|
| usuario_id, token, plataforma | services/notifications.py |
| fecha_registro (default/trigger en DB, nunca se escribe desde la app excepto por `ON CONFLICT DO UPDATE`) | services/notifications.py |

Constraint esperado: `UNIQUE (usuario_id, token)` — el `INSERT ... ON CONFLICT (usuario_id, token) DO UPDATE` depende de que exista esa unique constraint.

## `notificaciones`
| Columna | Usada en |
|---|---|
| id, usuario_id | services/notifications.py |
| tipo, titulo, mensaje, data_extra (JSON) | services/notifications.py |
| leida (BOOLEAN) | services/notifications.py |
| fecha_creacion | services/notifications.py |

## Cómo verificar esto contra tu base real

En `psql` contra tu instancia de Azure:

```sql
\d padres
\d children
\d tasks
\d task_assignments
\d device_policies
\d device_tokens
\d notificaciones
```

Si alguna columna de esta tabla no aparece en el `\d` real (y no es una de las
marcadas "nueva"), hay un desfase que **no** se puede detectar con los tests
actuales (mockean la base) y causará un 500 real. Avísame y lo corregimos
antes de la demo.
