"""Catálogo y vacunaciones por HTTP."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_mascotas import _especie_id, _crear_cliente, _crear_mascota


def test_crear_y_filtrar_vacunas(client: TestClient, db: Session) -> None:
    """El catálogo persiste especies y filtra por especie aplicable."""
    perro = _especie_id(db)
    gato = _especie_id(db, "GATO")
    respuesta = client.post("/api/vacunas", json={
        "nombre": "Antirrábica", "obligatoria": True, "especies_aplicables": [perro],
    })
    assert respuesta.status_code == 201
    vacuna = respuesta.json()
    assert vacuna["nombre"] == "Antirrábica"
    assert vacuna["especies_aplicables"] == [{"id": perro, "nombre": "PERRO"}]
    assert client.get("/api/vacunas").json() == [vacuna]
    assert client.get("/api/vacunas", params={"especie_id": perro}).json() == [vacuna]
    assert client.get("/api/vacunas", params={"especie_id": gato}).json() == []


def test_vacuna_con_especie_inexistente(client: TestClient) -> None:
    """Una especie inexistente impide guardar el alta."""
    respuesta = client.post("/api/vacunas", json={
        "nombre": "Prueba", "obligatoria": False, "especies_aplicables": [999999],
    })
    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()
    assert client.get("/api/vacunas").json() == []


def test_nombre_vacuna_duplicado(client: TestClient, db: Session) -> None:
    """El nombre único genera conflicto sin modificar el catálogo."""
    datos = {"nombre": "Única", "especies_aplicables": [_especie_id(db)]}
    assert client.post("/api/vacunas", json=datos).status_code == 201
    assert client.post("/api/vacunas", json=datos).status_code == 409
    assert len(client.get("/api/vacunas").json()) == 1


def test_filtro_especie_invalido(client: TestClient) -> None:
    """El filtro exige un identificador entero."""
    assert client.get("/api/vacunas?especie_id=texto").status_code == 422


def test_registrar_y_listar_vacunaciones(client: TestClient, db: Session) -> None:
    """La aplicación persiste en la historia elegida."""
    duenio = _crear_cliente(client)
    mascota = _crear_mascota(client, duenio["id"], _especie_id(db))
    historia = client.get(f"/api/mascotas/{mascota['id']}/historia-clinica").json()
    vacuna = client.post("/api/vacunas", json={
        "nombre": "Antirrábica", "especies_aplicables": [_especie_id(db)],
    }).json()
    ruta = f"/api/historias-clinicas/{historia['id']}/vacunaciones"
    assert client.get(ruta).json() == []
    respuesta = client.post(ruta, json={"vacuna_id": vacuna["id"], "fecha": "2026-01-01"})
    assert respuesta.status_code == 201
    aplicacion = respuesta.json()
    assert aplicacion["vacuna_id"] == vacuna["id"]
    assert aplicacion["historia_clinica_id"] == historia["id"]
    assert aplicacion["fecha"] == "2026-01-01"
    assert client.get(ruta).json() == [aplicacion]
    assert client.post(ruta, json={"vacuna_id": 999999, "fecha": "2026-01-01"}).status_code == 404
    assert client.get(ruta).json() == [aplicacion]


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_vacunaciones_historia_inexistente(client: TestClient, metodo: str) -> None:
    """Ambas operaciones requieren una historia existente."""
    argumentos = {"json": {"vacuna_id": 1, "fecha": "2026-01-01"}} if metodo == "post" else {}
    respuesta = client.request(metodo, "/api/historias-clinicas/999999/vacunaciones", **argumentos)
    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


def test_vacunas_pendientes_por_especie(client: TestClient, db: Session) -> None:
    """La consulta descuenta aplicaciones y excluye vacunas de otra especie."""
    perro = _especie_id(db)
    gato = _especie_id(db, "GATO")
    duenio = _crear_cliente(client)
    mascota = _crear_mascota(client, duenio["id"], perro)
    historia = client.get(f"/api/mascotas/{mascota['id']}/historia-clinica").json()
    base = f"/api/historias-clinicas/{historia['id']}"
    assert client.get(base + "/vacunas-pendientes").json() == []
    obligatoria = client.post("/api/vacunas", json={
        "nombre": "Obligatoria", "obligatoria": True, "especies_aplicables": [perro],
    }).json()
    for nombre, requerida, especie in [("Opcional", False, perro), ("Felina", True, gato)]:
        assert client.post("/api/vacunas", json={
            "nombre": nombre, "obligatoria": requerida, "especies_aplicables": [especie],
        }).status_code == 201
    respuesta = client.get(base + "/vacunas-pendientes")
    assert respuesta.status_code == 200
    assert respuesta.json() == [obligatoria]
    assert client.post(base + "/vacunaciones", json={
        "vacuna_id": obligatoria["id"], "fecha": "2026-01-01",
    }).status_code == 201
    assert client.get(base + "/vacunas-pendientes").json() == []


def test_pendientes_historia_inexistente(client: TestClient) -> None:
    """La consulta de pendientes exige una historia existente."""
    respuesta = client.get("/api/historias-clinicas/999999/vacunas-pendientes")
    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()
