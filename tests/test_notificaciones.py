from datetime import datetime, timezone
from uuid import uuid4

import app.routers.notificaciones as notificaciones_router


def _fake_notificacion(usuario_id):
    return {
        "id": str(uuid4()),
        "usuario_id": str(usuario_id),
        "tipo": "TAREA_COMPLETADA",
        "titulo": "Tarea Completada",
        "mensaje": "Tu hijo completo una tarea",
        "data_extra": None,
        "leida": False,
        "fecha_creacion": datetime.now(timezone.utc).isoformat(),
    }


def test_get_notificaciones_accepts_padre_token(client, padre_token, monkeypatch):
    monkeypatch.setattr(
        notificaciones_router,
        "obtener_historial_notificaciones",
        lambda usuario_id: [_fake_notificacion(usuario_id)],
    )

    response = client.get("/api/notificaciones", headers={"Authorization": f"Bearer {padre_token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_notificaciones_accepts_child_token(client, child_token, monkeypatch):
    """Regresion: el token de hijo debe poder consultar sus notificaciones."""
    monkeypatch.setattr(
        notificaciones_router,
        "obtener_historial_notificaciones",
        lambda usuario_id: [_fake_notificacion(usuario_id)],
    )

    response = client.get("/api/notificaciones", headers={"Authorization": f"Bearer {child_token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_marcar_leidas_accepts_child_token(client, child_token, monkeypatch):
    called = {}
    monkeypatch.setattr(
        notificaciones_router,
        "marcar_como_leidas",
        lambda ids, usuario_id: called.update({"ids": ids, "usuario_id": usuario_id}),
    )

    response = client.put(
        "/api/notificaciones/leidas",
        json={"notificacion_ids": [str(uuid4())]},
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 200
    assert "ids" in called


def test_registrar_token_accepts_child_token(client, child_token, monkeypatch):
    monkeypatch.setattr(notificaciones_router, "registrar_device_token", lambda *a, **k: None)

    response = client.post(
        "/api/notificaciones/token",
        json={"token": "expo-token-123", "plataforma": "expo"},
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 201


def test_notificaciones_requires_auth(client):
    response = client.get("/api/notificaciones")

    assert response.status_code in (401, 403)


def test_test_endpoint_rejects_child_token(client, child_token):
    """El endpoint /test sigue siendo exclusivo de padres."""
    response = client.post(
        "/api/notificaciones/test",
        json={"tipo": "TAREA_COMPLETADA"},
        headers={"Authorization": f"Bearer {child_token}"},
    )

    assert response.status_code == 403
