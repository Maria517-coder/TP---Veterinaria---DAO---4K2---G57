"""Endpoints E44 a E47 de muestras y trazabilidad, de punta a punta por HTTP."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Cliente,
    ClinicaVeterinaria,
    Complejidad,
    ConsultaMedica,
    ContenedorEnvio,
    Especie,
    EstadoCatalogo,
    HistoriaClinica,
    Mascota,
    MuestraBiologica,
    RedVeterinaria,
    TipoMuestra,
    Veterinario,
)
from app.models.estados import Empaquetada, EnTransito, Recibida


@pytest.fixture()
def ctx(db: Session, client: TestClient) -> dict:
    """Reutiliza las semillas del lifespan y prepara dos muestras para HTTP."""
    red = db.scalar(select(RedVeterinaria))
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    tipo = db.scalar(select(TipoMuestra).where(TipoMuestra.nombre == "SANGRE"))
    estados = {fila.nombre: fila for fila in db.scalars(select(EstadoCatalogo))}
    hoy = datetime.now().date()
    clinica = ClinicaVeterinaria(nombre="Centro", red=red)
    db.add(clinica)
    db.flush()
    veterinario = Veterinario(
        nombre="Eva", matricula="MP-HTTP-MUESTRA", clinica=clinica
    )
    responsable = Cliente(nombre="Ana", telefono="123")
    db.add_all([veterinario, responsable])
    db.flush()
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=hoy - timedelta(days=365 * 3),
        responsable=responsable,
        especie=especie,
        historia_clinica=HistoriaClinica(numero=1),
    )
    db.add(mascota)
    db.flush()
    consulta = ConsultaMedica(
        numero=1,
        clinica=clinica,
        mascota=mascota,
        veterinario=veterinario,
        fecha=hoy,
        complejidad=Complejidad.BAJA,
        costo=Decimal("100.00"),
    )
    db.add(consulta)
    db.flush()
    contenedor = ContenedorEnvio(numero=1)
    db.add(contenedor)
    db.flush()
    extraida = MuestraBiologica(
        consulta=consulta,
        tipo=tipo,
        estado_actual=estados["Extraida"],
        contenedor=contenedor,
        fecha=hoy,
    )
    recibida = MuestraBiologica(
        consulta=consulta,
        tipo=tipo,
        estado_actual=estados["Extraida"],
        contenedor=contenedor,
        fecha=hoy,
    )
    db.add_all([extraida, recibida])
    db.flush()
    recibida.cambiar_estado(Empaquetada(), "Eva")
    recibida.cambiar_estado(EnTransito(), "Eva")
    recibida.cambiar_estado(Recibida(), "Eva")
    db.commit()
    return {
        "extraida_id": extraida.id,
        "recibida_id": recibida.id,
        "clinica_id": clinica.id,
        "contenedor_id": contenedor.id,
        "fecha": hoy,
    }


def _assert_error(respuesta: Response, codigo: int, texto: str = "") -> None:
    assert respuesta.status_code == codigo, respuesta.text
    assert "detalle" in respuesta.json()
    if texto:
        assert texto in respuesta.json()["detalle"]


def test_get_muestras_devuelve_200_con_las_muestras(client: TestClient, ctx: dict) -> None:
    respuesta = client.get("/api/muestras")

    assert respuesta.status_code == 200, respuesta.text
    cuerpos = respuesta.json()
    ids = {fila["id"] for fila in cuerpos}
    assert {ctx["extraida_id"], ctx["recibida_id"]} <= ids
    fila = next(fila for fila in cuerpos if fila["id"] == ctx["recibida_id"])
    assert fila["estado"] == "Recibida"
    assert fila["resultado"] is None
    assert fila["fecha_resultado"] is None


def test_get_muestras_combina_filtros_y_valida_el_estado(
    client: TestClient, ctx: dict
) -> None:
    respuesta = client.get(
        "/api/muestras",
        params={
            "estado": "Recibida",
            "clinica_id": ctx["clinica_id"],
            "contenedor_id": ctx["contenedor_id"],
            "fecha": ctx["fecha"].isoformat(),
        },
    )

    assert respuesta.status_code == 200, respuesta.text
    assert [fila["id"] for fila in respuesta.json()] == [ctx["recibida_id"]]

    sin_resultados = client.get("/api/muestras", params={"estado": "Analizada"})
    assert sin_resultados.status_code == 200
    assert sin_resultados.json() == []

    invalido = client.get("/api/muestras", params={"estado": "EnProceso"})
    assert invalido.status_code == 422


def test_get_muestra_por_id_devuelve_200_y_inexistente_da_404(
    client: TestClient, ctx: dict
) -> None:
    respuesta = client.get(f"/api/muestras/{ctx['extraida_id']}")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["id"] == ctx["extraida_id"]
    assert respuesta.json()["estado"] == "Extraida"

    _assert_error(client.get(f"/api/muestras/{ctx['extraida_id'] + 999}"), 404)


def test_get_historial_estados_devuelve_la_trazabilidad_y_404(
    client: TestClient, ctx: dict
) -> None:
    respuesta = client.get(f"/api/muestras/{ctx['recibida_id']}/historial-estados")

    assert respuesta.status_code == 200, respuesta.text
    historial = respuesta.json()
    assert [registro["estado"] for registro in historial] == [
        "Empaquetada",
        "EnTransito",
        "Recibida",
    ]
    assert all(registro["muestra_id"] == ctx["recibida_id"] for registro in historial)

    _assert_error(
        client.get(f"/api/muestras/{ctx['extraida_id'] + 999}/historial-estados"),
        404,
    )


def test_post_resultado_devuelve_200_con_la_muestra_actualizada(
    client: TestClient, ctx: dict
) -> None:
    respuesta = client.post(
        f"/api/muestras/{ctx['recibida_id']}/resultado",
        json={"texto": "  Negativo  ", "responsable": " Luis "},
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["id"] == ctx["recibida_id"]
    assert cuerpo["resultado"] == "Negativo"
    assert cuerpo["fecha_resultado"] == datetime.now().date().isoformat()
    assert cuerpo["estado"] == "Analizada"

    historial = client.get(f"/api/muestras/{ctx['recibida_id']}/historial-estados")
    assert historial.json()[-1]["responsable"] == "Luis"
    assert historial.json()[-1]["estado"] == "Analizada"


def test_post_resultado_rechaza_estado_y_cuerpo_invalido(
    client: TestClient, ctx: dict
) -> None:
    url = f"/api/muestras/{ctx['extraida_id']}/resultado"
    conflicto = client.post(
        url, json={"texto": "Negativo", "responsable": "Luis"}
    )
    _assert_error(conflicto, 409, "Recibida")

    sin_cambios = client.get(f"/api/muestras/{ctx['extraida_id']}")
    assert sin_cambios.json()["resultado"] is None
    assert sin_cambios.json()["estado"] == "Extraida"

    _assert_error(
        client.post(
            f"/api/muestras/{ctx['extraida_id'] + 999}/resultado",
            json={"texto": "Negativo", "responsable": "Luis"},
        ),
        404,
    )
    for cuerpo in (
        {"responsable": "Luis"},
        {"texto": "   ", "responsable": "Luis"},
        {"texto": "Negativo"},
        {"texto": "a" * 501, "responsable": "Luis"},
    ):
        assert client.post(url, json=cuerpo).status_code == 422
