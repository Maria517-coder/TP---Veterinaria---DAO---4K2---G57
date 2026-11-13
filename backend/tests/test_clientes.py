"""CRUD de clientes de punta a punta por HTTP."""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.especie import Especie
from app.models.mascota import Mascota


def _crear(cliente: TestClient, nombre: str = "Ana", telefono: str = "123") -> dict[str, object]:
    """Crea un cliente por HTTP y devuelve el cuerpo de la respuesta."""
    respuesta = cliente.post("/api/clientes", json={"nombre": nombre, "telefono": telefono})
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _assert_error_de_dominio(respuesta: Response, codigo: int) -> None:
    """Comprueba el código y el formato de error propio: {"detalle": "..."}."""
    assert respuesta.status_code == codigo, respuesta.text
    assert "detalle" in respuesta.json()


def test_crear_cliente(client: TestClient) -> None:
    """POST devuelve 201 con el cliente creado y activo."""
    respuesta = client.post("/api/clientes", json={"nombre": "Ana", "telefono": "123"})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id"] > 0
    assert cuerpo["nombre"] == "Ana"
    assert cuerpo["telefono"] == "123"
    assert cuerpo["activo"] is True


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"nombre": "", "telefono": "123"},
        {"nombre": "   ", "telefono": "123"},
        {"nombre": "Ana", "telefono": ""},
        {"nombre": "A" * 101, "telefono": "123"},
        {"nombre": "Ana", "telefono": "1" * 31},
    ],
)
def test_crear_cliente_invalido_da_422(client: TestClient, cuerpo: dict[str, str]) -> None:
    """Los datos inválidos los rechaza Pydantic con 422."""
    respuesta = client.post("/api/clientes", json=cuerpo)

    assert respuesta.status_code == 422


def test_obtener_cliente_por_id(client: TestClient) -> None:
    """GET por id devuelve el cliente existente."""
    creado = _crear(client)

    respuesta = client.get(f"/api/clientes/{creado['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Ana"


def test_obtener_cliente_inexistente_da_404(client: TestClient) -> None:
    """Un id que no existe devuelve 404."""
    _assert_error_de_dominio(client.get("/api/clientes/9999"), 404)


def test_listar_clientes(client: TestClient) -> None:
    """GET sin filtros devuelve todos los clientes activos."""
    _crear(client, "Ana", "111")
    _crear(client, "Bruno", "222")

    respuesta = client.get("/api/clientes")

    assert respuesta.status_code == 200
    assert {cliente["nombre"] for cliente in respuesta.json()} == {"Ana", "Bruno"}


def test_listar_clientes_filtra_por_nombre(client: TestClient) -> None:
    """El filtro por nombre es parcial y no distingue mayúsculas."""
    _crear(client, "Ana", "111")
    _crear(client, "Bruno", "222")

    respuesta = client.get("/api/clientes", params={"nombre": "an"})

    assert [cliente["nombre"] for cliente in respuesta.json()] == ["Ana"]


def test_actualizar_cliente(client: TestClient) -> None:
    """PUT reemplaza nombre y teléfono."""
    creado = _crear(client)

    respuesta = client.put(
        f"/api/clientes/{creado['id']}",
        json={"nombre": "Ana María", "telefono": "999"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Ana María"
    assert respuesta.json()["telefono"] == "999"


def test_actualizar_cliente_inexistente_da_404(client: TestClient) -> None:
    """PUT sobre un id inexistente devuelve 404."""
    respuesta = client.put(
        "/api/clientes/9999",
        json={"nombre": "Ana", "telefono": "123"},
    )

    _assert_error_de_dominio(respuesta, 404)


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"nombre": "", "telefono": "123"},
        {"nombre": "Ana", "telefono": "1" * 31},
    ],
)
def test_actualizar_cliente_invalido_da_422(
    client: TestClient, cuerpo: dict[str, str]
) -> None:
    """PUT también valida los datos con Pydantic."""
    creado = _crear(client)

    respuesta = client.put(f"/api/clientes/{creado['id']}", json=cuerpo)

    assert respuesta.status_code == 422


def test_eliminar_cliente(client: TestClient) -> None:
    """DELETE da de baja lógica: 204 y después el cliente ya no se encuentra."""
    creado = _crear(client)

    respuesta = client.delete(f"/api/clientes/{creado['id']}")

    assert respuesta.status_code == 204
    assert client.get(f"/api/clientes/{creado['id']}").status_code == 404


def test_eliminar_cliente_inexistente_da_404(client: TestClient) -> None:
    """DELETE sobre un id inexistente devuelve 404."""
    _assert_error_de_dominio(client.delete("/api/clientes/9999"), 404)


def test_eliminar_cliente_es_baja_logica(client: TestClient, db: Session) -> None:
    """DELETE no borra la fila: la marca como inactiva."""
    creado = _crear(client)

    assert client.delete(f"/api/clientes/{creado['id']}").status_code == 204

    en_bd = db.get(Cliente, creado["id"])
    assert en_bd is not None
    assert en_bd.activo is False


def test_eliminar_cliente_con_mascotas_da_409(client: TestClient, db: Session) -> None:
    """No se puede dar de baja un cliente que todavía tiene mascotas."""
    creado = _crear(client)
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    assert especie is not None
    db.add(
        Mascota(
            cliente_id=creado["id"],
            especie_id=especie.id,
            nombre="Luna",
            fecha_nacimiento=date(2020, 1, 1),
        )
    )
    db.commit()

    respuesta = client.delete(f"/api/clientes/{creado['id']}")

    _assert_error_de_dominio(respuesta, 409)


def test_eliminar_cliente_con_mascotas_inactivas_da_204(
    client: TestClient, db: Session
) -> None:
    """Las mascotas dadas de baja ya no bloquean la baja del cliente."""
    creado = _crear(client)
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    assert especie is not None
    mascota = Mascota(
        cliente_id=creado["id"],
        especie_id=especie.id,
        nombre="Luna",
        fecha_nacimiento=date(2020, 1, 1),
    )
    db.add(mascota)
    db.commit()

    assert client.delete(f"/api/mascotas/{mascota.id}").status_code == 204
    assert client.delete(f"/api/clientes/{creado['id']}").status_code == 204
