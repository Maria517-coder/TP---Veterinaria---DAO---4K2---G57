"""Prueba del endpoint de salud."""
from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        respuesta = client.get("/api/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}
