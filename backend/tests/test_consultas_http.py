"""Endpoints E36 a E43 de consultas y derivación, de punta a punta por HTTP."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.cliente import Cliente
from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.models.red_veterinaria import RedVeterinaria
from app.models.tipo_muestra import TipoMuestra
from app.models.vacuna import Vacuna
from app.models.veterinario import Veterinario


@pytest.fixture()
def ctx(db: Session, client: TestClient) -> dict:
    """Reutiliza los catálogos del lifespan y arma un consultorio mínimo."""
    red = db.scalar(select(RedVeterinaria))
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    tipo = db.scalar(select(TipoMuestra).where(TipoMuestra.nombre == "SANGRE"))
    assert red is not None and especie is not None and tipo is not None
    clinica = ClinicaVeterinaria(nombre="Centro HTTP", red=red)
    db.add(clinica)
    db.flush()
    veterinario = Veterinario(nombre="Eva", matricula="MP-HTTP-C1", clinica=clinica)
    responsable = Cliente(nombre="Ana", telefono="123")
    db.add_all([veterinario, responsable])
    db.flush()
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=datetime.now().date() - timedelta(days=730),
        responsable=responsable,
        especie=especie,
        historia_clinica=HistoriaClinica(numero=1),
    )
    db.add(mascota)
    db.commit()
    return {
        "clinica": clinica.id,
        "vet": veterinario.id,
        "mascota": mascota.id,
        "historia": mascota.historia_clinica.id,
        "tipo": tipo.id,
        "hoy": datetime.now().date(),
    }


def _post(client: TestClient, ctx: dict, **cambios) -> Response:
    base = {
        "veterinario_id": ctx["vet"],
        "mascota_id": ctx["mascota"],
        "fecha": (ctx["hoy"] - timedelta(days=1)).isoformat(),
        "complejidad": "BAJA",
        "costo": "100.00",
    }
    base.update(cambios)
    return client.post("/api/consultas", json=base)


def _crear(client: TestClient, ctx: dict, **cambios) -> dict:
    respuesta = _post(client, ctx, **cambios)
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _assert_error(respuesta: Response, codigo: int) -> None:
    assert respuesta.status_code == codigo, respuesta.text
    # Los errores de dominio usan "detalle"; los de Pydantic, "detail".
    cuerpo = respuesta.json()
    assert "detalle" in cuerpo or "detail" in cuerpo


def _agregar_vacuna_obligatoria(db: Session, ctx: dict) -> Vacuna:
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    vacuna = Vacuna(
        nombre="Rabia HTTP", obligatoria=True, especies_aplicables=[especie]
    )
    db.add(vacuna)
    db.commit()
    return vacuna


def test_post_consulta_devuelve_201_con_aviso(client: TestClient, ctx: dict,
                                              db: Session) -> None:
    vacuna = _agregar_vacuna_obligatoria(db, ctx)

    respuesta = _post(client, ctx)

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["numero"] == 1
    assert cuerpo["clinica_id"] == ctx["clinica"]
    assert cuerpo["veterinario_id"] == ctx["vet"]
    assert cuerpo["mascota_id"] == ctx["mascota"]
    assert cuerpo["costo"] == "100.00"  # Decimal se serializa como texto.
    assert cuerpo["vacunas_pendientes"] == [{"id": vacuna.id, "nombre": "Rabia HTTP"}]


def test_post_consulta_con_esquema_completo(client: TestClient, ctx: dict,
                                            db: Session) -> None:
    vacuna = _agregar_vacuna_obligatoria(db, ctx)
    historia = db.get(HistoriaClinica, ctx["historia"])
    historia.registrar_vacunacion(vacuna, ctx["hoy"] - timedelta(days=30))
    db.commit()

    cuerpo = _crear(client, ctx)

    assert cuerpo["vacunas_pendientes"] == []


def test_post_consulta_no_exige_turno(client: TestClient, ctx: dict) -> None:
    assert _post(client, ctx).status_code == 201


def test_post_consulta_veterinario_inexistente(client: TestClient, ctx: dict) -> None:
    _assert_error(_post(client, ctx, veterinario_id=9999), 404)


def test_post_consulta_mascota_inexistente(client: TestClient, ctx: dict) -> None:
    _assert_error(_post(client, ctx, mascota_id=9999), 404)


def test_post_consulta_fecha_futura(client: TestClient, ctx: dict) -> None:
    _assert_error(_post(client, ctx, fecha=(ctx["hoy"] + timedelta(days=1)).isoformat()), 422)


def test_post_consulta_costo_float(client: TestClient, ctx: dict) -> None:
    _assert_error(_post(client, ctx, costo=100.5), 422)


def test_get_consultas_con_filtros_combinables(client: TestClient, ctx: dict) -> None:
    ayer = (ctx["hoy"] - timedelta(days=1)).isoformat()
    anteayer = (ctx["hoy"] - timedelta(days=2)).isoformat()
    a = _crear(client, ctx, fecha=ayer)
    b = _crear(client, ctx, fecha=anteayer)
    assert client.post(
        f"/api/consultas/{a['id']}/muestras", json={"tipo_muestra_id": ctx["tipo"]}
    ).status_code == 201

    respuesta = client.get("/api/consultas")
    assert respuesta.status_code == 200
    assert [item["id"] for item in respuesta.json()] == [a["id"], b["id"]]

    filtrada = client.get(
        "/api/consultas",
        params={
            "veterinario_id": ctx["vet"],
            "mascota_id": ctx["mascota"],
            "fecha": ayer,
            "con_muestras": True,
        },
    )
    assert filtrada.status_code == 200
    assert [item["id"] for item in filtrada.json()] == [a["id"]]


def test_get_consulta_por_id(client: TestClient, ctx: dict) -> None:
    creada = _crear(client, ctx)

    respuesta = client.get(f"/api/consultas/{creada['id']}")
    assert respuesta.status_code == 200
    assert respuesta.json()["numero"] == 1
    _assert_error(client.get("/api/consultas/9999"), 404)


def test_post_muestra_201_y_errores(client: TestClient, ctx: dict) -> None:
    consulta = _crear(client, ctx)

    respuesta = client.post(
        f"/api/consultas/{consulta['id']}/muestras",
        json={"tipo_muestra_id": ctx["tipo"]},
    )
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["consulta_id"] == consulta["id"]
    assert cuerpo["tipo_muestra_id"] == ctx["tipo"]
    assert cuerpo["estado"] == "Extraida"
    assert cuerpo["resultado"] is None

    _assert_error(
        client.post(
            "/api/consultas/9999/muestras", json={"tipo_muestra_id": ctx["tipo"]}
        ),
        404,
    )
    _assert_error(
        client.post(
            f"/api/consultas/{consulta['id']}/muestras",
            json={"tipo_muestra_id": 9999},
        ),
        404,
    )


def test_get_muestras_200_y_404(client: TestClient, ctx: dict) -> None:
    consulta = _crear(client, ctx)
    muestra = client.post(
        f"/api/consultas/{consulta['id']}/muestras",
        json={"tipo_muestra_id": ctx["tipo"]},
    ).json()

    respuesta = client.get(f"/api/consultas/{consulta['id']}/muestras")
    assert respuesta.status_code == 200
    assert [item["id"] for item in respuesta.json()] == [muestra["id"]]
    _assert_error(client.get("/api/consultas/9999/muestras"), 404)


def test_orden_derivacion_pdf_y_409(client: TestClient, ctx: dict) -> None:
    consulta = _crear(client, ctx)

    _assert_error(client.get(f"/api/consultas/{consulta['id']}/orden-derivacion"), 409)

    client.post(
        f"/api/consultas/{consulta['id']}/muestras",
        json={"tipo_muestra_id": ctx["tipo"]},
    )
    respuesta = client.get(f"/api/consultas/{consulta['id']}/orden-derivacion")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/pdf")
    assert respuesta.content.startswith(b"%PDF")
    assert len(respuesta.content) > 0
    _assert_error(client.get("/api/consultas/9999/orden-derivacion"), 404)


def test_comprobante_pdf(client: TestClient, ctx: dict) -> None:
    consulta = _crear(client, ctx)

    respuesta = client.get(f"/api/consultas/{consulta['id']}/comprobante")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/pdf")
    assert respuesta.content.startswith(b"%PDF")
    assert len(respuesta.content) > 0
    _assert_error(client.get("/api/consultas/9999/comprobante"), 404)


def test_costo_total_200_y_404(client: TestClient, ctx: dict) -> None:
    consulta = _crear(client, ctx)

    sin_muestras = client.get(f"/api/consultas/{consulta['id']}/costo-total")
    assert sin_muestras.status_code == 200
    assert sin_muestras.json() == {"costo_total": "100.00"}

    client.post(
        f"/api/consultas/{consulta['id']}/muestras",
        json={"tipo_muestra_id": ctx["tipo"]},
    )
    con_muestras = client.get(f"/api/consultas/{consulta['id']}/costo-total")
    assert con_muestras.json() == {"costo_total": "1600.00"}
    _assert_error(client.get("/api/consultas/9999/costo-total"), 404)
