"""Descarga del carnet de vacunas por HTTP."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_mascotas import _crear_cliente, _crear_mascota, _especie_id


def test_descargar_carnet(client: TestClient, db: Session) -> None:
    """Una mascota existente obtiene un documento PDF descargable."""
    responsable = _crear_cliente(client, nombre="María & José")
    mascota = _crear_mascota(client, responsable["id"], _especie_id(db))
    respuesta = client.get(f"/api/mascotas/{mascota['id']}/carnet-vacunas")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/pdf"
    assert respuesta.headers["content-disposition"] == (
        f"attachment; filename=carnet-vacunas-{mascota['id']}.pdf"
    )
    assert respuesta.content.startswith(b"%PDF-")
    assert respuesta.content.rstrip().endswith(b"%%EOF")


def test_carnet_mascota_inexistente(client: TestClient) -> None:
    """Una mascota inexistente produce el error de dominio 404."""
    respuesta = client.get("/api/mascotas/999999/carnet-vacunas")
    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


def test_carnet_mascota_inactiva(client: TestClient, db: Session) -> None:
    """La descarga mantiene el criterio de consulta de mascotas activas."""
    responsable = _crear_cliente(client)
    mascota = _crear_mascota(client, responsable["id"], _especie_id(db))
    assert client.delete(f"/api/mascotas/{mascota['id']}").status_code == 204
    respuesta = client.get(f"/api/mascotas/{mascota['id']}/carnet-vacunas")
    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()
