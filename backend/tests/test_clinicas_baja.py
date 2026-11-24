"""Tests de baja lógica de clínicas (Bloque G)."""
import pytest


def test_eliminar_clinica_da_404_si_no_existe(client, db):
    r = client.delete("/api/clinicas/9999")
    assert r.status_code == 404


def test_eliminar_clinica_baja_logica_y_no_aparece(client, db):
    r = client.post("/api/red/clinicas", json={"nombre": "Clinica Baja"})
    assert r.status_code == 201
    cid = r.json()["id"]

    r = client.delete(f"/api/clinicas/{cid}")
    assert r.status_code == 204

    r = client.get(f"/api/clinicas/{cid}")
    assert r.status_code == 404

    r = client.get("/api/clinicas")
    assert all(c["id"] != cid for c in r.json())


def test_eliminar_clinica_con_veterinarios_activos_da_409(client, db):
    r = client.post("/api/red/clinicas", json={"nombre": "Clinica Con Vet"})
    cid = r.json()["id"]
    r = client.post(
        f"/api/clinicas/{cid}/veterinarios",
        json={"matricula": "MAT-1", "nombre": "Vet Uno"},
    )
    assert r.status_code == 201

    r = client.delete(f"/api/clinicas/{cid}")
    assert r.status_code == 409
    assert "veterinarios activos" in r.json()["detalle"].lower()


def test_clinica_inactiva_no_admite_veterinarios_nuevos(client, db):
    r = client.post("/api/red/clinicas", json={"nombre": "Clinica Inactiva"})
    cid = r.json()["id"]
    assert client.delete(f"/api/clinicas/{cid}").status_code == 204

    r = client.post(
        f"/api/clinicas/{cid}/veterinarios",
        json={"matricula": "MAT-X", "nombre": "Vet X"},
    )
    assert r.status_code == 404
