-- Ejecutar después de 001_recompensas_logros_avatar.sql, antes de desplegar.
BEGIN;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS color TEXT;
ALTER TABLE device_policies ADD COLUMN IF NOT EXISTS sleep_enabled BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE task_assignments ADD COLUMN IF NOT EXISTS earned_keys INTEGER;
ALTER TABLE task_assignments ADD COLUMN IF NOT EXISTS earned_minutes INTEGER;
UPDATE task_assignments ta SET
    earned_keys = COALESCE(ta.earned_keys, t.reward_keys, 0),
    earned_minutes = COALESCE(ta.earned_minutes, COALESCE(t.duration_hours, 0) * 60 + COALESCE(t.duration_minutes, 0))
FROM tasks t WHERE ta.task_id = t.id AND ta.status = 'verified'
AND (ta.earned_keys IS NULL OR ta.earned_minutes IS NULL);
UPDATE device_policies SET sleep_days = replace(replace(replace(replace(replace(replace(replace(sleep_days,
    'Mon', 'Lun'), 'Tue', 'Mar'), 'Wed', 'Mie'), 'Thu', 'Jue'), 'Fri', 'Vie'), 'Sat', 'Sab'), 'Sun', 'Dom');
COMMIT;
