import json
import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests
import time
import urllib.parse
import hmac
import hashlib
import base64
from app.database import get_connection
from app.config import settings

logger = logging.getLogger(__name__)

def registrar_device_token(usuario_id: UUID, token: str, plataforma: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO device_tokens (usuario_id, token, plataforma) VALUES (%s, %s, %s) ON CONFLICT (usuario_id, token) DO UPDATE SET fecha_registro = CURRENT_TIMESTAMP",
                (str(usuario_id), token, plataforma)
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al guardar device token: {e}")
        raise e
    finally:
        conn.close()

def _generar_sas_token(uri: str, key_name: str, key_value: str) -> str:
    target_uri = urllib.parse.quote_plus(uri).encode('utf-8')
    sas_key = key_value.encode('utf-8')
    
    # Token válido por 1 hora
    expiry = str(int(time.time() + 3600))
    string_to_sign = target_uri + b'\n' + expiry.encode('utf-8')
    
    signature = base64.b64encode(hmac.new(sas_key, string_to_sign, hashlib.sha256).digest())
    signature_url_encoded = urllib.parse.quote(signature)
    
    return f"SharedAccessSignature sr={urllib.parse.quote_plus(uri)}&sig={signature_url_encoded}&se={expiry}&skn={key_name}"

def _parsear_connection_string(conn_str: str):
    parts = dict(part.split('=', 1) for part in conn_str.split(';') if '=' in part)
    endpoint = parts.get("Endpoint", "").replace("sb://", "https://")
    if not endpoint.endswith("/"):
        endpoint += "/"
    return endpoint, parts.get("SharedAccessKeyName", ""), parts.get("SharedAccessKey", "")

def enviar_notificacion(
    usuario_id: UUID, 
    tipo: str, 
    titulo: str, 
    mensaje: str, 
    data_extra: Optional[Dict[str, Any]] = None
):
    conn = get_connection()
    # Guardar en Base de Datos
    try:
        with conn.cursor() as cur:
            data_json = json.dumps(data_extra) if data_extra else None
            cur.execute("INSERT INTO notificaciones (usuario_id, tipo, titulo, mensaje, data_extra) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (str(usuario_id), tipo, titulo, mensaje, data_json)
            )
            result = cur.fetchone()
            if result:
                notificacion_id = dict(result)['id']  # Type hint fix

            # Buscar tokens del usuario para enviarle la push
            cur.execute("SELECT token, plataforma FROM device_tokens WHERE usuario_id = %s", (str(usuario_id),))
            rows = cur.fetchall()
            # Type hint fix
            tokens_dispositivos = [{"token": dict(row)['token'], "plataforma": dict(row)['plataforma']} for row in rows]
            
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al guardar notificación: {e}")
        conn.close()
        return False
    finally:
        conn.close()

    # Azure Notification Hubs
    hub_name = settings.AZURE_NH_NAME
    conn_str = settings.AZURE_NH_CONNECTION_STRING

    if not conn_str or not hub_name or "sb://" not in conn_str:
        logger.warning("Faltan variables de Azure NH en .env, notificación guardada pero no se envió push.")
        return True

    endpoint, key_name, key_value = _parsear_connection_string(conn_str)
    
    # Endpoint para Direct Send (enviar directamente a un token de dispositivo)
    url = f"{endpoint}{hub_name}/messages/?direct&api-version=2015-01"
    auth_token = _generar_sas_token(endpoint, key_name, key_value)

    for device in tokens_dispositivos:
        plataforma = device['plataforma']
        token = device['token']
        
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json;charset=utf-8",
            "ServiceBusNotification-DeviceHandle": token
        }
        
        if plataforma == 'android':
            headers["ServiceBusNotification-Format"] = "gcm"
            payload = {
                "data": {
                    "tipo": tipo,
                    "title": titulo,
                    "body": mensaje,
                    "extra": data_extra
                }
            }
        elif plataforma == 'ios':
            headers["ServiceBusNotification-Format"] = "apple"
            payload = {
                "aps": {
                    "alert": {
                        "title": titulo,
                        "body": mensaje
                    }
                },
                "tipo": tipo,
                "extra": data_extra
            }
        else:
            continue

        # Realizar la petición POST a la nube
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code in (200, 201):
                logger.info(f"Push enviada exitosamente a {plataforma} ({token[:10]}...)")
            else:
                logger.error(f"Fallo envío Push Azure ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Error HTTP comunicando con Azure: {e}")

    return True

def obtener_historial_notificaciones(usuario_id: UUID):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM notificaciones WHERE usuario_id = %s ORDER BY fecha_creacion DESC", 
                (str(usuario_id),)
            )
            return cur.fetchall()
    finally:
        conn.close()

def marcar_como_leidas(notificacion_ids: List[UUID]):
    if not notificacion_ids: return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Cast a UUID str
            ids_str = tuple(str(uid) for uid in notificacion_ids)
            cur.execute(
                "UPDATE notificaciones SET leida = TRUE WHERE id IN %s",
                (ids_str,)
            )
            conn.commit()
    finally:
        conn.close()
