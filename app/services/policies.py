"""Creación de políticas para perfiles anteriores a esta funcionalidad."""


def ensure_device_policy(cursor, child_id):
    """El llamador debe bloquear children antes para serializar la creación."""
    cursor.execute(
        """INSERT INTO device_policies
            (child_id, available_screen_time_minutes, sleep_start_time, sleep_end_time,
             sleep_days, restricted_apps, created_at, updated_at)
            SELECT %s, 0, '21:30:00', '07:30:00', 'Lun,Mar,Mie,Jue,Vie,Sab,Dom', '[]', NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM device_policies WHERE child_id = %s)""",
        (str(child_id), str(child_id)),
    )
