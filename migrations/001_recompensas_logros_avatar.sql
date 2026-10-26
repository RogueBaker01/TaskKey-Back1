-- Migracion: llaves, avatar del hijo y evidencia de fotos
--
-- IMPORTANTE: este repo no tiene una herramienta de migraciones (Alembic, etc.),
-- la base de datos vive en Azure Database for PostgreSQL y se administra a mano.
-- Hay que correr este script (y 002_pantallas_conectadas.sql despues) contra esa
-- base ANTES de desplegar el codigo que los usa (app/routers/actividad.py,
-- los cambios en tareas.py/auth_hijos.py/hijos.py).
--
-- Es seguro correrlo varias veces (usa IF NOT EXISTS).
--
-- Nota: "recompensas" se implemento como el historial de llaves/minutos ganados
-- al verificar tareas (ver app/routers/actividad.py GET /mis-recompensas), no
-- como una tienda de canjes, asi que no hace falta un catalogo de recompensas
-- ni una tabla de canjes.

-- 1) Balance de llaves del hijo (se acredita al verificar una tarea)
ALTER TABLE children ADD COLUMN IF NOT EXISTS llaves_disponibles INTEGER NOT NULL DEFAULT 0;

-- 2) Avatar del hijo (id de un catalogo fijo que vive en el backend)
ALTER TABLE children ADD COLUMN IF NOT EXISTS avatar_id TEXT;

-- 3) Evidencia (foto en base64) de una tarea completada, enviada por el hijo
ALTER TABLE task_assignments ADD COLUMN IF NOT EXISTS evidencia_foto TEXT;
