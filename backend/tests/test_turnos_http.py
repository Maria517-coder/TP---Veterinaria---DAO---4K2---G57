"""Endpoints E32 a E35 de agenda y turnos, de punta a punta por HTTP."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.models.red_veterinaria import RedVeterinaria
from app.models.veterinario import Veterinario


@pytest.fixture()
def ctx(db: Session, client: TestClient) -> dict:
    """Reutiliza las semillas del lifespan y arma el grafo de turnos."""
    red = db.scalar(select(RedVeterinaria))
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    clinica = ClinicaVeterinaria(nombre="Centro", red=red)
    db.add(clinica)
    db.flush()
    veterinario = Veterinario(nombre="Eva", matricula="MP-HTTP-1", clinica=clinica)
    veterinario_baja = Veterinario(
        nombre="Baja", matricula="MP-HTTP-2", clinica=clinica, activo=False
    )
    responsable = Cliente(nombre="Ana", telefono="123")
    db.add_all([veterinario, veterinario_baja, responsable])
    db.flush()
    nacimiento = datetime.now().date() - timedelta(days=365)
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=nacimiento,
        responsable=responsable,
        especie=especie,
        historia_clinica=HistoriaClinica(numero=1),
    )
    mascota_baja = Mascota(
        nombre="Sol",
        fecha_nacimiento=nacimiento,
        responsable=responsable,
        especie=especie,
        activo=False,
        historia_clinica=HistoriaClinica(numero=2),
    )
    db.add_all([mascota, mascota_baja])
    db.commit()
    return {
        "vet": veterinario.id,
        "vet_baja": veterinario_baja.id,
        "mascota": mascota.id,
        "mascota_baja": mascota_baja.id,
        "base": (datetime.now() + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        ),
    }


def _post(
    client: TestClient, ctx: dict, desde: int = 0, hasta: int = 30, mascota_id=None
) -> Response:
    base = ctx["base"]
    return client.post(
        f"/api/veterinarios/{ctx['vet']}/turnos",
        json={
            "mascota_id": mascota_id if mascota_id is not None else ctx["mascota"],
            "inicio": (base + timedelta(minutes=desde)).isoformat(),
            "fin": (base + timedelta(minutes=hasta)).isoformat(),
        },
    )


def _assert_error(respuesta: Response, codigo: int) -> None:
    assert respuesta.status_code == codigo, respuesta.text
    assert "detalle" in respuesta.json()


def test_post_turno_devuelve_201(client: TestClient, ctx: dict) -> None:
    respuesta = _post(client, ctx)

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["id"] > 0
    assert cuerpo["veterinario_id"] == ctx["vet"]
    assert cuerpo["mascota_id"] == ctx["mascota"]
    assert cuerpo["activo"] is True
    assert "inicio" in cuerpo and "fin" in cuerpo


def test_post_turno_invalido_da_422(client: TestClient, ctx: dict) -> None:
    base = ctx["base"]
    assert _post(client, ctx, 0, 0).status_code == 422
    assert _post(client, ctx, 0, -30).status_code == 422
    assert _post(client, ctx, mascota_id=0).status_code == 422
    respuesta = client.post(
        f"/api/veterinarios/{ctx['vet']}/turnos",
        json={
            "mascota_id": ctx["mascota"],
            "inicio": (datetime.now() - timedelta(seconds=1)).isoformat(),
            "fin": (base + timedelta(minutes=30)).isoformat(),
        },
    )
    assert respuesta.status_code == 422


def test_post_veterinario_inexistente_o_inactivo_da_404(
    client: TestClient, ctx: dict
) -> None:
    base = ctx["base"]
    cuerpo = {
        "mascota_id": ctx["mascota"],
        "inicio": base.isoformat(),
        "fin": (base + timedelta(minutes=30)).isoformat(),
    }

    _assert_error(client.post("/api/veterinarios/9999/turnos", json=cuerpo), 404)
    _assert_error(
        client.post(f"/api/veterinarios/{ctx['vet_baja']}/turnos", json=cuerpo), 404
    )


def test_post_mascota_inexistente_o_inactiva_da_404(
    client: TestClient, ctx: dict
) -> None:
    _assert_error(_post(client, ctx, mascota_id=9999), 404)
    _assert_error(_post(client, ctx, mascota_id=ctx["mascota_baja"]), 404)


def test_post_turno_superpuesto_da_409(client: TestClient, ctx: dict) -> None:
    assert _post(client, ctx, 0, 60).status_code == 201

    _assert_error(_post(client, ctx, 30, 90), 409)


def test_get_agenda_devuelve_200_filtra_y_ordena(
    client: TestClient, ctx: dict
) -> None:
    cancelado = _post(client, ctx, 0, 30).json()
    segundo = _post(client, ctx, 60, 90).json()
    primero = _post(client, ctx, 120, 150).json()
    assert client.delete(f"/api/turnos/{cancelado['id']}").status_code == 204

    respuesta = client.get(f"/api/veterinarios/{ctx['vet']}/agenda")
    assert respuesta.status_code == 200
    assert [turno["id"] for turno in respuesta.json()] == [
        segundo["id"],
        primero["id"],
    ]

    fecha = ctx["base"].date().isoformat()
    con_fecha = client.get(f"/api/veterinarios/{ctx['vet']}/agenda?fecha={fecha}")
    assert con_fecha.status_code == 200
    assert [turno["id"] for turno in con_fecha.json()] == [
        segundo["id"],
        primero["id"],
    ]
    sin_turnos = client.get(
        f"/api/veterinarios/{ctx['vet']}/agenda"
        f"?fecha={(ctx['base'] + timedelta(days=2)).date().isoformat()}"
    )
    assert sin_turnos.json() == []


def test_get_agenda_veterinario_inactivo_da_404(
    client: TestClient, ctx: dict
) -> None:
    _assert_error(client.get(f"/api/veterinarios/{ctx['vet_baja']}/agenda"), 404)


def test_get_disponibilidad_devuelve_200(client: TestClient, ctx: dict) -> None:
    base = ctx["base"]

    def consultar(desde: int, hasta: int) -> Response:
        return client.get(
            f"/api/veterinarios/{ctx['vet']}/turnos/disponibilidad",
            params={
                "inicio": (base + timedelta(minutes=desde)).isoformat(),
                "fin": (base + timedelta(minutes=hasta)).isoformat(),
            },
        )

    libre = consultar(0, 30)
    assert libre.status_code == 200
    assert libre.json() == {"disponible": True}

    assert _post(client, ctx, 0, 60).status_code == 201
    ocupado = consultar(30, 90)
    assert ocupado.status_code == 200
    assert ocupado.json() == {"disponible": False}
    assert consultar(60, 90).json() == {"disponible": True}


def test_delete_turno_devuelve_204_y_es_baja_logica(
    client: TestClient, ctx: dict
) -> None:
    turno = _post(client, ctx).json()

    respuesta = client.delete(f"/api/turnos/{turno['id']}")

    assert respuesta.status_code == 204
    assert respuesta.content == b""
    assert client.get(f"/api/veterinarios/{ctx['vet']}/agenda").json() == []
    _assert_error(client.delete(f"/api/turnos/{turno['id']}"), 404)


def test_delete_turno_inexistente_da_404(client: TestClient, ctx: dict) -> None:
    _assert_error(client.delete("/api/turnos/9999"), 404)
