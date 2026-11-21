"""Endpoints E48 a E52 de contenedores, con tests directos de service y repository."""
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
from app.repositories.contenedor_repository import ContenedorRepository
from app.seeds.datos_iniciales import cargar_datos_iniciales
from app.services.contenedor_service import ContenedorService


@pytest.fixture()
def ctx(db: Session, client: TestClient) -> dict:
    """Semillas relativas en fecha, dos clínicas y tres muestras Extraida."""
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
            nombre=f"Vet{indice}", matricula=f"MP-C3-{indice}", clinica=clinica
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

    muestras = []
    for consulta, fecha in (
        (consultas[0], hoy),
        (consultas[0], hoy),
        (consultas[1], hoy - timedelta(days=10)),
    ):
        muestra = MuestraBiologica(
            consulta=consulta,
            tipo=tipo,
            estado_actual=estados["Extraida"],
            fecha=fecha,
        )
        db.add(muestra)
        db.flush()
        muestras.append(muestra)
    db.commit()

    return {
        "db": db,
        "client": client,
        "hoy": hoy,
        "clinicas": clinicas,
        "m1": muestras[0].id,
        "m2": muestras[1].id,
        "m3": muestras[2].id,
        "clinica1_id": clinicas[0].id,
    }


def _crear_contenedor(client: TestClient) -> int:
    respuesta = client.post("/api/contenedores", json={})
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


def _assert_error(respuesta: Response, codigo: int, texto: str = "") -> None:
    assert respuesta.status_code == codigo, respuesta.text
    assert "detalle" in respuesta.json()
    if texto:
        assert texto in respuesta.json()["detalle"]


def test_post_contenedores_crea_con_precinto_intacto_y_numero_correlativo(
    client: TestClient, ctx: dict
) -> None:
    primera = client.post("/api/contenedores", json={})
    segunda = client.post("/api/contenedores", json={})

    assert primera.status_code == 201, primera.text
    assert primera.json() == {
        "id": primera.json()["id"],
        "numero": 1,
        "precinto_intacto": True,
        "remito_id": None,
        "cantidad_muestras": 0,
    }
    assert segunda.status_code == 201, segunda.text
    assert segunda.json()["numero"] == 2
    assert ContenedorRepository(ctx["db"]).siguiente_numero() == 3


def test_get_contenedores_filtra_por_remito_y_fechas(client: TestClient, ctx: dict) -> None:
    c1 = _crear_contenedor(client)
    c2 = _crear_contenedor(client)
    assert client.post(
        f"/api/contenedores/{c1}/muestras",
        json={"muestra_id": ctx["m1"], "responsable": "Eva"},
    ).status_code == 200
    assert client.post(
        f"/api/contenedores/{c2}/muestras",
        json={"muestra_id": ctx["m3"], "responsable": "Eva"},
    ).status_code == 200

    db: Session = ctx["db"]
    contenedor = db.get(ContenedorEnvio, c1)
    remito = RemitoBiologico(
        numero=1,
        fecha_emision=datetime.now(),
        clinica_origen_id=ctx["clinica1_id"],
        laboratorio_destino="Lab",
        estado=EstadoRemito.GENERADO,
        contenedor=contenedor,
    )
    db.add(remito)
    db.commit()

    con_remito = client.get("/api/contenedores", params={"con_remito": "true"})
    sin_remito = client.get("/api/contenedores", params={"con_remito": "false"})
    desde = client.get("/api/contenedores", params={"desde": ctx["hoy"].isoformat()})
    hasta = client.get(
        "/api/contenedores",
        params={"hasta": (ctx["hoy"] - timedelta(days=1)).isoformat()},
    )

    assert [fila["id"] for fila in con_remito.json()] == [c1]
    assert [fila["id"] for fila in sin_remito.json()] == [c2]
    assert [fila["id"] for fila in desde.json()] == [c1]
    assert [fila["id"] for fila in hasta.json()] == [c2]


def test_get_contenedor_por_id_y_404(client: TestClient, ctx: dict) -> None:
    contenedor_id = _crear_contenedor(client)

    respuesta = client.get(f"/api/contenedores/{contenedor_id}")
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["id"] == contenedor_id

    _assert_error(client.get(f"/api/contenedores/{contenedor_id + 999}"), 404)


def test_post_muestras_agrega_y_valida_reglas(client: TestClient, ctx: dict) -> None:
    contenedor_id = _crear_contenedor(client)

    respuesta = client.post(
        f"/api/contenedores/{contenedor_id}/muestras",
        json={"muestra_id": ctx["m1"], "responsable": "  Eva  "},
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["cantidad_muestras"] == 1
    assert client.get(f"/api/muestras/{ctx['m1']}").json()["estado"] == "Empaquetada"

    _assert_error(
        client.post(
            f"/api/contenedores/{contenedor_id}/muestras",
            json={"muestra_id": ctx["m3"], "responsable": "Eva"},
        ),
        422,
        "misma clínica",
    )
    _assert_error(
        client.post(
            f"/api/contenedores/{contenedor_id}/muestras",
            json={"muestra_id": ctx["m1"], "responsable": "Eva"},
        ),
        409,
        "Extraida",
    )
    _assert_error(
        client.post(
            f"/api/contenedores/{contenedor_id}/muestras",
            json={"muestra_id": 999999, "responsable": "Eva"},
        ),
        404,
    )
    assert client.post(
        f"/api/contenedores/{contenedor_id}/muestras",
        json={"muestra_id": ctx["m2"], "responsable": "   "},
    ).status_code == 422


@pytest.mark.parametrize("estado", [EstadoRemito.RECIBIDO, EstadoRemito.CERRADO])
def test_romper_precinto_se_bloquea_tras_recepcion(
    client: TestClient, ctx: dict, estado: EstadoRemito
) -> None:
    contenedor_id = _crear_contenedor(client)
    db: Session = ctx["db"]
    db.add(
        RemitoBiologico(
            numero=20 + list(EstadoRemito).index(estado),
            fecha_emision=datetime.now(),
            clinica_origen_id=ctx["clinica1_id"],
            laboratorio_destino="Lab",
            estado=estado,
            contenedor=db.get(ContenedorEnvio, contenedor_id),
        )
    )
    db.commit()

    _assert_error(
        client.post(f"/api/contenedores/{contenedor_id}/romper-precinto"),
        409,
        "recepción",
    )


def test_romper_precinto_es_irreversible_y_permitido_en_transito(
    client: TestClient, ctx: dict
) -> None:
    contenedor_id = _crear_contenedor(client)
    roto = client.post(f"/api/contenedores/{contenedor_id}/romper-precinto")
    assert roto.status_code == 200, roto.text
    assert roto.json()["precinto_intacto"] is False
    _assert_error(
        client.post(f"/api/contenedores/{contenedor_id}/romper-precinto"),
        409,
        "ya está roto",
    )

    en_transito = _crear_contenedor(client)
    db: Session = ctx["db"]
    db.add(
        RemitoBiologico(
            numero=30,
            fecha_emision=datetime.now(),
            clinica_origen_id=ctx["clinica1_id"],
            laboratorio_destino="Lab",
            estado=EstadoRemito.DESPACHADO,
            contenedor=db.get(ContenedorEnvio, en_transito),
        )
    )
    db.commit()
    respuesta = client.post(f"/api/contenedores/{en_transito}/romper-precinto")
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["precinto_intacto"] is False


def test_service_y_repository_directos(db: Session, ctx: dict) -> None:
    from app.schemas.contenedor import ContenedorCrear, ContenedorFiltros, MuestraAgregar

    service = ContenedorService(db)
    contenedor = service.crear(ContenedorCrear())
    assert contenedor.numero == 1
    assert service.listar(ContenedorFiltros()) == [contenedor]
    assert service.obtener(contenedor.id) is contenedor

    service.agregar_muestra(
        contenedor.id,
        MuestraAgregar(muestra_id=ctx["m1"], responsable="Eva"),
    )
    db.refresh(contenedor)
    assert [muestra.id for muestra in contenedor.muestras] == [ctx["m1"]]

    service.romper_precinto(contenedor.id)
    db.refresh(contenedor)
    assert contenedor.precinto_intacto is False
    assert ContenedorRepository(db).siguiente_numero() == 2


def test_post_generar_remito_crea_generado_y_valida(client: TestClient, ctx: dict) -> None:
    contenedor_id = _crear_contenedor(client)
    ruta = f"/api/contenedores/{contenedor_id}/remito"

    _assert_error(
        client.post(ruta, json={"laboratorio_destino": "Lab"}),
        409,
        "no tiene muestras",
    )
    respuesta_invalida = client.post(ruta, json={"laboratorio_destino": "   "})
    assert respuesta_invalida.status_code == 422, respuesta_invalida.text

    for muestra_id in (ctx["m1"], ctx["m2"]):
        assert client.post(
            f"/api/contenedores/{contenedor_id}/muestras",
            json={"muestra_id": muestra_id, "responsable": "Eva"},
        ).status_code == 200

    respuesta = client.post(ruta, json={"laboratorio_destino": "  Lab Norte  "})
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["estado"] == "GENERADO"
    assert respuesta.json()["laboratorio_destino"] == "Lab Norte"
    assert respuesta.json()["numero"] == 1
    assert respuesta.json()["contenedor_id"] == contenedor_id

    _assert_error(
        client.post(ruta, json={"laboratorio_destino": "Otro lab"}),
        409,
        "ya tiene un remito",
    )
    _assert_error(
        client.post(
            "/api/contenedores/999999/remito", json={"laboratorio_destino": "Lab"}
        ),
        404,
    )


def test_get_remito_del_contenedor(client: TestClient, ctx: dict) -> None:
    contenedor_id = _crear_contenedor(client)
    ruta = f"/api/contenedores/{contenedor_id}/remito"

    _assert_error(client.get(ruta), 404, "no tiene remito")
    assert client.post(
        f"/api/contenedores/{contenedor_id}/muestras",
        json={"muestra_id": ctx["m1"], "responsable": "Eva"},
    ).status_code == 200
    assert client.post(
        ruta, json={"laboratorio_destino": "Lab Central"}
    ).status_code == 201

    respuesta = client.get(ruta)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "GENERADO"
    assert respuesta.json()["laboratorio_destino"] == "Lab Central"

    _assert_error(client.get("/api/contenedores/999999/remito"), 404)
