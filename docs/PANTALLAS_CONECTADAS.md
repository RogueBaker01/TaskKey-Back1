# Conexión de pantallas

El frontend `Taskey-Front` consume la API para los datos de negocio; no devuelve datos de ejemplo ni utiliza caché local como respuesta exitosa cuando falla una lectura de API. Las sesiones y borradores de foto sí requieren almacenamiento local.

## Contratos nuevos

| Pantalla | Endpoint | Datos |
| --- | --- | --- |
| Perfil del hijo | GET `/actividad/mi-resumen` | Perfil, saldo, política, racha y contadores |
| Recompensas | GET `/actividad/mis-recompensas` | Saldo de llaves/minutos e historial de tareas verificadas |
| Logros | GET `/actividad/mis-logros` | Objetivos y cumplimiento calculados por el servidor |
| Progreso | GET `/actividad/mi-progreso-mensual` | Tres meses; verificadas/asignadas por mes de asignación UTC |
| Avatar | GET `/actividad/avatares`, PUT `/actividad/mi-avatar` | Catálogo gratuito y selección persistida |
| Restricciones | GET `/policies/catalogo/apps` | Catálogo común para ambas pantallas del padre |

Los endpoints `/actividad` requieren token del hijo y usan exclusivamente su identidad autenticada. Las políticas y el catálogo de aplicaciones requieren token del padre; la política valida propiedad del hijo.

Las recompensas son el historial de lo ganado al verificar tareas, no una tienda de canjes. Los logros actuales son primera misión, diez misiones aprobadas y racha de tres días; no se atribuyen categorías de ejercicio o educación que no están modeladas.

## Flujos conectados

- Crear/editar tareas guarda también el color y permite quitar fechas opcionales. Un error no cierra el formulario.
- Asignar y desasignar desde administración y desde el perfil del hijo invoca la API.
- La cámara genera JPEG base64. El borrador queda en memoria hasta enviar `evidencia_foto` con el estado `completed`. El padre consulta la evidencia persistida antes de aprobar. Fotos limitadas a 4 millones de caracteres.
- La verificación bloquea la asignación durante la transacción, acredita una sola vez y guarda los valores de llaves/minutos ganados. Una asignación verificada no se puede reabrir. La notificación se envía después de confirmar la transacción.
- Se guarda un horario por hijo. Eliminar lo desactiva mediante `sleep_enabled=false`; los cambios de restricciones conservan el resto de la política.
- Las rutas antiguas de tabs reutilizan las pantallas conectadas.
- No se implementa el bloqueo nativo del dispositivo ni consumo real de minutos.

## Base de datos y despliegue pendientes

Por instrucción del usuario no se conecta con Azure ni se aplican migraciones en esta tarea. La base temporal creada durante el trabajo se detuvo y eliminó.

Antes de usar este código contra Azure, revisar/aplicar en orden:

1. `migrations/001_recompensas_logros_avatar.sql` (ya existía en el trabajo local).
2. `migrations/002_pantallas_conectadas.sql` (color de tarea, horario habilitado y valores de premios acreditados).

La segunda migración rellena los valores históricos de tareas verificadas usando los valores actuales de esas tareas; no reconstruye ediciones pasadas ni corrige saldos históricos. No ejecutarla sin revisar los datos existentes.

Configurar `API_URL` del frontend con el backend desplegado y las variables habituales del backend. Queda pendiente la validación de persistencia contra Azure y la prueba de cámara/push en dispositivos físicos. Las pruebas automatizadas de esta entrega aíslan API/DB; no sustituyen esa validación.
