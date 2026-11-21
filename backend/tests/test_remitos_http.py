"""Endpoints E55 a E60 de remitos, con tests directos de service y repository."""
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
    EstadoRemito,
    HistoriaClinica,
    Mascota,
    MuestraBiologica,
    RedVeterinaria,
    RemitoBiologico,
    TipoMuestra,
    Veterinario,
)
from app.seeds.datos_iniciales import cargar_datos_iniciales


@pytest.fixture()
def ctx(db: Session, client: TestClient) -> dict:
    """Dos contenedores con dos muestras Empaquetada y su remito GENERADO (fechas relativas)."""
    cargar_datos_iniciales(db)
    db.commit()
    red = db.scalar(select(RedVeterinaria))
    tipo = db.scalar(select(TipoMuestra).where(TipoMuestra.nombre == "SANGRE"))
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    estados = {fila.nombre: fila for fila in db.scalars(select(EstadoCatalogo))}
    hoy = datetime.now().date()

    clinicas = [
        ClinicaVeterinaria(nombre="Centro", red=red),
        ClinicaVeterinaria(nombre="Oeste", red=red),
    ]
    responsable = Cliente(nombre="Ana", telefono="123")
    db.add_all([*clinicas, responsable])
    db.flush()

    consultas = []
    for indice, clinica in enumerate(clinicas, start=1):
        veterinario = Veterinario(
            nombre=f"Vet{indice}", matricula=f"MP-R4-{indice}", clinica=clinica
        )
        mascota = Mascota(
            nombre=f"M{indice}",
            fecha_nacimiento=hoy - timedelta(days=365 * 3),
            responsable=responsable,
            especie=especie,
            historia_clinica=HistoriaClinica(numero=indice),
        )
        db.add_all([veterinario, mascota])
        db.flush()
        consulta = ConsultaMedica(
            numero=indice,
            clinica=clinica,
            mascota=mascota,
            veterinario=veterinario,
            fecha=hoy,
            complejidad=Complejidad.BAJA,
            costo=Decimal("100.00"),
        )
        db.add(consulta)
        db.flush()
        consultas.append(consulta)

    contenedores = []
    remitos = []
    muestras = []
    for indice, consulta in enumerate(consultas, start=1):
        contenedor = ContenedorEnvio(numero=indice)
        db.add(contenedor)
        db.flush()
        for _ in range(2):
            muestra = MuestraBiologica(
                consulta=consulta,
                tipo=tipo,
                estado_actual=estados["Extraida"],
                fecha=hoy,
            )
            db.add(muestra)
            db.flush()
            contenedor.agregar_muestra(muestra, "Eva")
            muestras.append(muestra.id)
        remito = contenedor.generar_remito(f"Lab {indice}", indice)
        db.add(remito)
        db.flush()
        remito.fecha_emision = datetime.now() - timedelta(days=10 * (indice - 1))
        contenedores.append(contenedor.id)
        remitos.append(remito.id)
    db.commit()

    return {
        "db": db,
        "client": client,
        "hoy": hoy,
        "clinica1_id": clinicas[0].id,
        "clinica2_id": clinicas[1].id,
        "contenedor1_id": contenedores[0],
        "contenedor2_id": contenedores[1],
        "remito1_id": remitos[0],
        "remito2_id": remitos[1],
        "muestra1_id": muestras[0],
        "muestra3_id": muestras[2],
    }


def _assert_error(respuesta: Response, codigo: int, texto: str = "") -> None:
    assert respuesta.status_code == codigo, respuesta.text
    assert "detalle" in respuesta.json()
    if texto:
        assert texto in respuesta.json()["detalle"]


def test_get_remitos_filtra_por_estado_clinica_y_fechas(
    client: TestClient, ctx: dict
) -> None:
    assert client.post(
        f"/api/remitos/{ctx['remito1_id']}/despachar", json={"responsable": "Eva"}
    ).status_code == 200

    generados = client.get("/api/remitos", params={"estado": "GENERADO"})
    despachados = client.get("/api/remitos", params={"estado": "DESPACHADO"})
    de_clinica1 = client.get("/api/remitos", params={"clinica_id": ctx["clinica1_id"]})
    de_clinica2 = client.get("/api/remitos", params={"clinica_id": ctx["clinica2_id"]})
    desde = client.get("/api/remitos", params={"desde": ctx["hoy"].isoformat()})
    hasta = client.get(
        "/api/remitos", params={"hasta": (ctx["hoy"] - timedelta(days=1)).isoformat()}
    )

    assert [fila["id"] for fila in generados.json()] == [ctx["remito2_id"]]
    assert [fila["id"] for fila in despachados.json()] == [ctx["remito1_id"]]
    assert [fila["id"] for fila in de_clinica1.json()] == [ctx["remito1_id"]]
    assert [fila["id"] for fila in de_clinica2.json()] == [ctx["remito2_id"]]
    assert [fila["id"] for fila in desde.json()] == [ctx["remito1_id"]]
    assert [fila["id"] for fila in hasta.json()] == [ctx["remito2_id"]]


def test_get_remito_por_id_y_404(client: TestClient, ctx: dict) -> None:
    respuesta = client.get(f"/api/remitos/{ctx['remito1_id']}")
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["numero"] == 1
    assert respuesta.json()["estado"] == "GENERADO"
    assert respuesta.json()["contenedor_id"] == ctx["contenedor1_id"]

    _assert_error(client.get(f"/api/remitos/{ctx['remito1_id'] + 999}"), 404)


def test_get_remito_imprimir_devuelve_pdf(client: TestClient, ctx: dict) -> None:
    respuesta = client.get(f"/api/remitos/{ctx['remito1_id']}/imprimir")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["content-type"].startswith("application/pdf")
    assert respuesta.content.startswith(b"%PDF")

    _assert_error(client.get("/api/remitos/999999/imprimir"), 404)


def test_post_despachar_cambia_estado_y_valida(client: TestClient, ctx: dict) -> None:
    remito_id = ctx["remito1_id"]
    # El 422 de validación de Pydantic usa la clave "detail" (no "detalle").
    respuesta_invalida = client.post(
        f"/api/remitos/{remito_id}/despachar", json={"responsable": "   "}
    )
    assert respuesta_invalida.status_code == 422, respuesta_invalida.text

    respuesta = client.post(
        f"/api/remitos/{remito_id}/despachar", json={"responsable": "  Eva  "}
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "DESPACHADO"
    assert respuesta.json()["fecha_hora_despacho"] is not None
    assert (
        client.get(f"/api/muestras/{ctx['muestra1_id']}").json()["estado"] == "EnTransito"
    )

    _assert_error(
        client.post(f"/api/remitos/{remito_id}/despachar", json={"responsable": "Eva"}),
        409,
        "GENERADO",
    )
    _assert_error(
        client.post("/api/remitos/999999/despachar", json={"responsable": "Eva"}),
        404,
    )


def test_post_recepcion_devuelve_estado_final_segun_precinto(
    client: TestClient, ctx: dict
) -> None:
    remito_id = ctx["remito1_id"]
    _assert_error(
        client.post(f"/api/remitos/{remito_id}/recepcion", json={"responsable": "Luis"}),
        409,
        "DESPACHADO",
    )
    client.post(f"/api/remitos/{remito_id}/despachar", json={"responsable": "Eva"})

    respuesta = client.post(
        f"/api/remitos/{remito_id}/recepcion", json={"responsable": "  Luis  "}
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "RECIBIDO"
    assert respuesta.json()["fecha_hora_recepcion"] is not None
    assert (
        client.get(f"/api/muestras/{ctx['muestra1_id']}").json()["estado"] == "Recibida"
    )
    _assert_error(
        client.post(f"/api/remitos/{remito_id}/recepcion", json={"responsable": "Luis"}),
        409,
        "DESPACHADO",
    )

    roto = ctx["remito2_id"]
    assert client.post(
        f"/api/contenedores/{ctx['contenedor2_id']}/romper-precinto"
    ).status_code == 200
    client.post(f"/api/remitos/{roto}/despachar", json={"responsable": "Eva"})
    respuesta = client.post(f"/api/remitos/{roto}/recepcion", json={"responsable": "Luis"})

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "CERRADO"
    assert (
        client.get(f"/api/muestras/{ctx['muestra3_id']}").json()["estado"] == "Rechazada"
    )


def test_get_tiempo_transito_devuelve_segundos_y_409_sin_fechas(
    client: TestClient, ctx: dict
) -> None:
    remito_id = ctx["remito1_id"]
    _assert_error(client.get(f"/api/remitos/{remito_id}/tiempo-transito"), 409, "despacho")

    cliente = client.post(
        f"/api/remitos/{remito_id}/despachar", json={"responsable": "Eva"}
    )
    assert cliente.status_code == 200
    db: Session = ctx["db"]
    remito = db.get(RemitoBiologico, remito_id)
    remito.fecha_hora_despacho = datetime.now() - timedelta(seconds=90)
    db.commit()
    _assert_error(
        client.get(f"/api/remitos/{remito_id}/tiempo-transito"), 409, "recepción"
    )

    assert client.post(
        f"/api/remitos/{remito_id}/recepcion", json={"responsable": "Luis"}
    ).status_code == 200
    respuesta = client.get(f"/api/remitos/{remito_id}/tiempo-transito")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json() == {"tiempo_transito": pytest.approx(90.0, abs=2.0)}


def test_service_y_repository_directos(db: Session, ctx: dict) -> None:
    from app.repositories.remito_repository import RemitoRepository
    from app.schemas.remito import RemitoFiltros, ResponsableAccion
    from app.services.remito_service import RemitoService

    repositorio = RemitoRepository(db)
    servicio = RemitoService(db)

    assert repositorio.siguiente_numero() == 3
    assert len(repositorio.listar()) == 2
    assert repositorio.buscar_por_id(ctx["remito1_id"]).numero == 1
    assert repositorio.buscar_por_contenedor(ctx["contenedor1_id"]).id == ctx["remito1_id"]
    assert repositorio.buscar_por_id(999999) is None
    assert len(servicio.listar(RemitoFiltros(estado=EstadoRemito.GENERADO))) == 2
    assert servicio.obtener(ctx["remito1_id"]).estado is EstadoRemito.GENERADO
    assert isinstance(servicio.imprimir(ctx["remito1_id"]), bytes)

    servicio.despachar(ctx["remito1_id"], ResponsableAccion(responsable="Eva"))
    db.refresh(repositorio.buscar_por_id(ctx["remito1_id"]))
    assert servicio.obtener(ctx["remito1_id"]).estado is EstadoRemito.DESPACHADO

    servicio.recepcionar(ctx["remito1_id"], ResponsableAccion(responsable="Luis"))
    assert servicio.obtener(ctx["remito1_id"]).estado is EstadoRemito.RECIBIDO
    assert servicio.tiempo_transito(ctx["remito1_id"]) >= 0
