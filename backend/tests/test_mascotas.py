"""CRUD de mascotas de punta a punta por HTTP."""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.models import ClinicaVeterinaria, ConsultaMedica, RedVeterinaria, Veterinario
from app.models.complejidad import Complejidad


def _crear_cliente(
    cliente: TestClient, nombre: str = "Ana", telefono: str = "123"
) -> dict[str, object]:
    """Crea un cliente por HTTP y devuelve el cuerpo de la respuesta."""
    respuesta = cliente.post(
        "/api/clientes", json={"nombre": nombre, "telefono": telefono}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _especie_id(db: Session, nombre: str = "PERRO") -> int:
    """Devuelve el id de una especie sembrada por el lifespan."""
    especie = db.scalar(select(Especie).where(Especie.nombre == nombre))
    assert especie is not None
    return especie.id


def _crear_mascota(
    cliente: TestClient,
    cliente_id: int,
    especie_id: int,
    nombre: str = "Luna",
    fecha_nacimiento: str = "2020-01-01",
) -> dict[str, object]:
    """Crea una mascota por HTTP y devuelve el cuerpo de la respuesta."""
    respuesta = cliente.post(
        "/api/mascotas",
        json={
            "cliente_id": cliente_id,
            "especie_id": especie_id,
            "nombre": nombre,
            "fecha_nacimiento": fecha_nacimiento,
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _assert_error_de_dominio(respuesta: Response, codigo: int) -> None:
    """Comprueba el código y el formato de error propio: {"detalle": "..."}."""
    assert respuesta.status_code == codigo, respuesta.text
    assert "detalle" in respuesta.json()


def test_obtener_historia_clinica(client: TestClient, db: Session) -> None:
    """GET devuelve la historia creada junto con la mascota solicitada."""
    duenio = _crear_cliente(client)
    mascota = _crear_mascota(client, duenio["id"], _especie_id(db))
    historia = db.scalar(
        select(HistoriaClinica).where(HistoriaClinica.mascota_id == mascota["id"])
    )
    assert historia is not None

    respuesta = client.get(f"/api/mascotas/{mascota['id']}/historia-clinica")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "id": historia.id,
        "mascota_id": mascota["id"],
        "numero": historia.numero,
    }


def test_historia_clinica_de_mascota_inexistente(client: TestClient) -> None:
    """GET informa el error de dominio cuando la mascota no existe."""
    respuesta = client.get("/api/mascotas/999999/historia-clinica")

    _assert_error_de_dominio(respuesta, 404)


def test_historia_clinica_de_mascota_inactiva(client: TestClient, db: Session) -> None:
    """GET respeta la baja lógica usada para consultar mascotas."""
    duenio = _crear_cliente(client)
    mascota = _crear_mascota(client, duenio["id"], _especie_id(db))
    assert client.delete(f"/api/mascotas/{mascota['id']}").status_code == 204

    respuesta = client.get(f"/api/mascotas/{mascota['id']}/historia-clinica")

    _assert_error_de_dominio(respuesta, 404)


def test_listar_consultas_de_historia_vacia(client: TestClient, db: Session) -> None:
    """Una historia existente sin atenciones devuelve una lista vacía."""
    duenio = _crear_cliente(client)
    mascota = _crear_mascota(client, duenio["id"], _especie_id(db))
    historia = client.get(f"/api/mascotas/{mascota['id']}/historia-clinica").json()
    respuesta = client.get(f"/api/historias-clinicas/{historia['id']}/consultas")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_consultas_de_historia_inexistente(client: TestClient) -> None:
    """Una historia inexistente produce el error de dominio 404."""
    respuesta = client.get("/api/historias-clinicas/999999/consultas")
    _assert_error_de_dominio(respuesta, 404)


def test_consultas_corresponden_a_la_historia(client: TestClient, db: Session) -> None:
    """E13 devuelve los datos guardados y excluye consultas de otra mascota."""
    duenio = _crear_cliente(client)
    mascota = _crear_mascota(client, duenio["id"], _especie_id(db))
    otra = _crear_mascota(client, duenio["id"], _especie_id(db), nombre="Sol")
    historia = client.get(f"/api/mascotas/{mascota['id']}/historia-clinica").json()
    red = db.scalars(select(RedVeterinaria)).one()
    clinica = ClinicaVeterinaria(nombre="Central", red=red)
    veterinario = Veterinario(nombre="Ana", matricula="MAT-1", clinica=clinica)
    consultas = [
        ConsultaMedica(numero=numero, clinica=clinica, veterinario=veterinario,
                       mascota_id=datos["id"], fecha=date(2026, 1, 1),
                       complejidad=Complejidad.BAJA, costo="100.00")
        for numero, datos in enumerate([mascota, otra], start=1)
    ]
    db.add_all(consultas)
    db.commit()
    respuesta = client.get(f"/api/historias-clinicas/{historia['id']}/consultas")
    assert respuesta.status_code == 200
    assert respuesta.json() == [{
        "id": consultas[0].id, "numero": 1, "clinica_id": clinica.id,
        "veterinario_id": veterinario.id, "mascota_id": mascota["id"],
        "fecha": "2026-01-01", "complejidad": "BAJA", "costo": "100.00",
    }]


def test_crear_mascota(client: TestClient, db: Session) -> None:
    """POST crea la mascota, su historia clínica y las relaciona por número."""
    duenio = _crear_cliente(client)
    especie_id = _especie_id(db)

    respuesta = client.post(
        "/api/mascotas",
        json={
            "cliente_id": duenio["id"],
            "especie_id": especie_id,
            "nombre": "  Luna  ",
            "fecha_nacimiento": "2020-01-01",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["id"] > 0
    assert cuerpo["cliente_id"] == duenio["id"]
    assert cuerpo["especie_id"] == especie_id
    assert cuerpo["nombre"] == "Luna"
    assert cuerpo["fecha_nacimiento"] == "2020-01-01"
    assert cuerpo["activo"] is True

    db.expire_all()
    historia = db.scalar(
        select(HistoriaClinica).where(HistoriaClinica.mascota_id == cuerpo["id"])
    )
    assert historia is not None
    assert historia.numero == cuerpo["id"]


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {
            "cliente_id": 1,
            "especie_id": 1,
            "nombre": "",
            "fecha_nacimiento": "2020-01-01",
        },
        {
            "cliente_id": 1,
            "especie_id": 1,
            "nombre": "   ",
            "fecha_nacimiento": "2020-01-01",
        },
        {
            "cliente_id": 1,
            "especie_id": 1,
            "nombre": "Luna",
            "fecha_nacimiento": "no-es-fecha",
        },
        {
            "cliente_id": 1,
            "especie_id": 1,
            "nombre": "L" * 101,
            "fecha_nacimiento": "2020-01-01",
        },
    ],
)
def test_crear_mascota_invalida_da_422(
    client: TestClient, cuerpo: dict[str, object]
) -> None:
    """Los datos inválidos los rechaza Pydantic con 422."""
    assert client.post("/api/mascotas", json=cuerpo).status_code == 422


def test_crear_mascota_con_cliente_inexistente_da_404(
    client: TestClient, db: Session
) -> None:
    """Un responsable que no existe devuelve 404."""
    respuesta = client.post(
        "/api/mascotas",
        json={
            "cliente_id": 9999,
            "especie_id": _especie_id(db),
            "nombre": "Luna",
            "fecha_nacimiento": "2020-01-01",
        },
    )

    _assert_error_de_dominio(respuesta, 404)


def test_crear_mascota_con_cliente_inactivo_da_404(
    client: TestClient, db: Session
) -> None:
    """Un responsable dado de baja se comporta como inexistente."""
    duenio = _crear_cliente(client)
    assert client.delete(f"/api/clientes/{duenio['id']}").status_code == 204

    respuesta = client.post(
        "/api/mascotas",
        json={
            "cliente_id": duenio["id"],
            "especie_id": _especie_id(db),
            "nombre": "Luna",
            "fecha_nacimiento": "2020-01-01",
        },
    )

    _assert_error_de_dominio(respuesta, 404)


def test_crear_mascota_con_especie_inexistente_da_404(client: TestClient) -> None:
    """Una especie que no existe devuelve 404."""
    duenio = _crear_cliente(client)

    respuesta = client.post(
        "/api/mascotas",
        json={
            "cliente_id": duenio["id"],
            "especie_id": 9999,
            "nombre": "Luna",
            "fecha_nacimiento": "2020-01-01",
        },
    )

    _assert_error_de_dominio(respuesta, 404)


def test_listar_mascotas_solo_activas(client: TestClient, db: Session) -> None:
    """GET sin filtros devuelve las mascotas activas."""
    duenio = _crear_cliente(client)
    especie_id = _especie_id(db)
    _crear_mascota(client, duenio["id"], especie_id, "Luna")
    inactiva = _crear_mascota(client, duenio["id"], especie_id, "Michi")
    assert client.delete(f"/api/mascotas/{inactiva['id']}").status_code == 204

    respuesta = client.get("/api/mascotas")

    assert respuesta.status_code == 200
    assert [mascota["nombre"] for mascota in respuesta.json()] == ["Luna"]


def test_listar_mascotas_filtra_por_cliente_y_especie(
    client: TestClient, db: Session
) -> None:
    """GET acepta los filtros combinables cliente_id y especie_id."""
    ana = _crear_cliente(client, "Ana")
    bruno = _crear_cliente(client, "Bruno")
    perro = _especie_id(db, "PERRO")
    gato = _especie_id(db, "GATO")
    _crear_mascota(client, ana["id"], perro, "Luna")
    _crear_mascota(client, ana["id"], gato, "Michi")
    _crear_mascota(client, bruno["id"], perro, "Firulais")

    por_cliente = client.get("/api/mascotas", params={"cliente_id": ana["id"]})
    por_especie = client.get("/api/mascotas", params={"especie_id": gato})
    por_ambos = client.get(
        "/api/mascotas", params={"cliente_id": ana["id"], "especie_id": perro}
    )

    assert [m["nombre"] for m in por_cliente.json()] == ["Luna", "Michi"]
    assert [m["nombre"] for m in por_especie.json()] == ["Michi"]
    assert [m["nombre"] for m in por_ambos.json()] == ["Luna"]


def test_obtener_mascota_por_id(client: TestClient, db: Session) -> None:
    """GET por id devuelve la mascota existente."""
    duenio = _crear_cliente(client)
    creada = _crear_mascota(client, duenio["id"], _especie_id(db))

    respuesta = client.get(f"/api/mascotas/{creada['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Luna"


def test_obtener_mascota_inexistente_da_404(client: TestClient) -> None:
    """Un id que no existe devuelve 404."""
    _assert_error_de_dominio(client.get("/api/mascotas/9999"), 404)


def test_obtener_mascota_inactiva_da_404(client: TestClient, db: Session) -> None:
    """Una mascota dada de baja se comporta como inexistente."""
    duenio = _crear_cliente(client)
    creada = _crear_mascota(client, duenio["id"], _especie_id(db))
    assert client.delete(f"/api/mascotas/{creada['id']}").status_code == 204

    _assert_error_de_dominio(client.get(f"/api/mascotas/{creada['id']}"), 404)


def test_actualizar_mascota(client: TestClient, db: Session) -> None:
    """PUT reemplaza responsable, especie, nombre y fecha de nacimiento."""
    duenio = _crear_cliente(client, "Ana")
    adoptante = _crear_cliente(client, "Bruno")
    perro = _especie_id(db, "PERRO")
    gato = _especie_id(db, "GATO")
    creada = _crear_mascota(client, duenio["id"], perro, "Luna")

    respuesta = client.put(
        f"/api/mascotas/{creada['id']}",
        json={
            "cliente_id": adoptante["id"],
            "especie_id": gato,
            "nombre": "Luna María",
            "fecha_nacimiento": "2021-02-03",
        },
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["cliente_id"] == adoptante["id"]
    assert cuerpo["especie_id"] == gato
    assert cuerpo["nombre"] == "Luna María"
    assert cuerpo["fecha_nacimiento"] == "2021-02-03"


def test_actualizar_mascota_inexistente_da_404(client: TestClient, db: Session) -> None:
    """PUT sobre un id inexistente devuelve 404."""
    respuesta = client.put(
        "/api/mascotas/9999",
        json={
            "cliente_id": 1,
            "especie_id": _especie_id(db),
            "nombre": "Luna",
            "fecha_nacimiento": "2020-01-01",
        },
    )

    _assert_error_de_dominio(respuesta, 404)


def test_actualizar_mascota_con_cliente_inexistente_da_404(
    client: TestClient, db: Session
) -> None:
    """PUT con un responsable inexistente devuelve 404."""
    duenio = _crear_cliente(client)
    creada = _crear_mascota(client, duenio["id"], _especie_id(db))

    respuesta = client.put(
        f"/api/mascotas/{creada['id']}",
        json={
            "cliente_id": 9999,
            "especie_id": _especie_id(db),
            "nombre": "Luna",
            "fecha_nacimiento": "2020-01-01",
        },
    )

    _assert_error_de_dominio(respuesta, 404)


def test_actualizar_mascota_con_especie_inexistente_da_404(
    client: TestClient, db: Session
) -> None:
    """PUT con una especie inexistente devuelve 404."""
    duenio = _crear_cliente(client)
    creada = _crear_mascota(client, duenio["id"], _especie_id(db))

    respuesta = client.put(
        f"/api/mascotas/{creada['id']}",
        json={
            "cliente_id": duenio["id"],
            "especie_id": 9999,
            "nombre": "Luna",
            "fecha_nacimiento": "2020-01-01",
        },
    )

    _assert_error_de_dominio(respuesta, 404)


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {
            "cliente_id": 1,
            "especie_id": 1,
            "nombre": "",
            "fecha_nacimiento": "2020-01-01",
        },
        {
            "cliente_id": 1,
            "especie_id": 1,
            "nombre": "Luna",
            "fecha_nacimiento": "no-es-fecha",
        },
    ],
)
def test_actualizar_mascota_invalida_da_422(
    client: TestClient, db: Session, cuerpo: dict[str, object]
) -> None:
    """PUT también valida los datos con Pydantic."""
    duenio = _crear_cliente(client)
    creada = _crear_mascota(client, duenio["id"], _especie_id(db))

    assert client.put(f"/api/mascotas/{creada['id']}", json=cuerpo).status_code == 422


def test_eliminar_mascota_es_baja_logica(client: TestClient, db: Session) -> None:
    """DELETE no borra la fila: la marca como inactiva."""
    duenio = _crear_cliente(client)
    creada = _crear_mascota(client, duenio["id"], _especie_id(db))

    assert client.delete(f"/api/mascotas/{creada['id']}").status_code == 204
    assert client.get(f"/api/mascotas/{creada['id']}").status_code == 404

    db.expire_all()
    en_bd = db.get(Mascota, creada["id"])
    assert en_bd is not None
    assert en_bd.activo is False


def test_eliminar_mascota_inexistente_da_404(client: TestClient) -> None:
    """DELETE sobre un id inexistente devuelve 404."""
    _assert_error_de_dominio(client.delete("/api/mascotas/9999"), 404)


def test_eliminar_mascota_inactiva_da_404(client: TestClient, db: Session) -> None:
    """Una segunda baja de la misma mascota devuelve 404."""
    duenio = _crear_cliente(client)
    creada = _crear_mascota(client, duenio["id"], _especie_id(db))
    assert client.delete(f"/api/mascotas/{creada['id']}").status_code == 204

    _assert_error_de_dominio(client.delete(f"/api/mascotas/{creada['id']}"), 404)


def test_listar_mascotas_de_un_cliente_solo_activas(
    client: TestClient, db: Session
) -> None:
    """GET /clientes/{id}/mascotas devuelve solo las mascotas activas del cliente."""
    ana = _crear_cliente(client, "Ana")
    bruno = _crear_cliente(client, "Bruno")
    especie_id = _especie_id(db)
    _crear_mascota(client, ana["id"], especie_id, "Luna")
    inactiva = _crear_mascota(client, ana["id"], especie_id, "Michi")
    _crear_mascota(client, bruno["id"], especie_id, "Firulais")
    assert client.delete(f"/api/mascotas/{inactiva['id']}").status_code == 204

    respuesta = client.get(f"/api/clientes/{ana['id']}/mascotas")

    assert respuesta.status_code == 200
    assert [mascota["nombre"] for mascota in respuesta.json()] == ["Luna"]


def test_listar_mascotas_de_cliente_inexistente_da_404(client: TestClient) -> None:
    """GET /clientes/{id}/mascotas de un cliente inexistente devuelve 404."""
    _assert_error_de_dominio(client.get("/api/clientes/9999/mascotas"), 404)


def test_listar_mascotas_de_cliente_inactivo_da_404(client: TestClient) -> None:
    """GET /clientes/{id}/mascotas de un cliente dado de baja devuelve 404."""
    ana = _crear_cliente(client)
    assert client.delete(f"/api/clientes/{ana['id']}").status_code == 204

    _assert_error_de_dominio(client.get(f"/api/clientes/{ana['id']}/mascotas"), 404)
