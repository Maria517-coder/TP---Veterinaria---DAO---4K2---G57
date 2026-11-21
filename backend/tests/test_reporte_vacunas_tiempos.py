"""E63 y E65: vacunas pendientes y tiempos promedio en segundos."""
from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CambioEstado,
    Cliente,
    ClinicaVeterinaria,
    ConsultaMedica,
    ContenedorEnvio,
    Especie,
    EstadoCatalogo,
    HistoriaClinica,
    Mascota,
    RedVeterinaria,
    RemitoBiologico,
    TipoMuestra,
    Vacuna,
    Veterinario,
)
from app.models.complejidad import Complejidad
from app.models.estado_remito import EstadoRemito
from app.reportes.reporte_tiempos_promedio import ReporteTiemposPromedio
from app.reportes.reporte_vacunas_pendientes import ReporteVacunasPendientes
from app.schemas.reporte import FiltroReporteRequest
from app.services.reporte_service import ReporteService

VACUNAS = "/api/reportes/vacunas-pendientes"
TIEMPOS = "/api/reportes/tiempos-promedio"
TRANSITO = "tiempo_transito_promedio_segundos"
PROCESAMIENTO = "tiempo_procesamiento_promedio_segundos"


def _estado(db: Session, nombre: str) -> EstadoCatalogo:
    """Obtiene o crea un estado del catálogo para armar el historial de tests."""
    estado = db.scalar(select(EstadoCatalogo).where(EstadoCatalogo.nombre == nombre))
    if estado is None:
        estado = EstadoCatalogo(nombre=nombre)
        db.add(estado)
        db.flush()
    return estado


@pytest.fixture()
def datos(db: Session) -> dict:
    """Datos relativos a hoy: vacunas y remitos despachados en distintos días."""
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    viejo = hoy - timedelta(days=10)
    red = db.scalar(select(RedVeterinaria).limit(1))
    if red is None:
        red = RedVeterinaria(nombre="Red G4")
        db.add(red)
        db.flush()
    centro = ClinicaVeterinaria(nombre="Centro G4", red=red)
    norte = ClinicaVeterinaria(nombre="Norte G4", red=red)
    db.add_all([centro, norte])
    db.flush()
    vet_centro = Veterinario(nombre="Ana G4", matricula="G4-1", clinica=centro)
    vet_norte = Veterinario(nombre="Luis G4", matricula="G4-2", clinica=norte)
    cliente = Cliente(nombre="Responsable G4", telefono="123")
    especie = Especie(nombre="PERRO-G4")
    rabia = Vacuna(nombre="Rabia G4", obligatoria=True, especies_aplicables=[especie])
    moquillo = Vacuna(nombre="Moquillo G4", obligatoria=True, especies_aplicables=[especie])
    opcional = Vacuna(nombre="Opcional G4", obligatoria=False, especies_aplicables=[especie])
    tipo = TipoMuestra(nombre="SANGRE-G4", costo_analisis="3.00")
    db.add_all([vet_centro, vet_norte, cliente, especie, rabia, moquillo, opcional, tipo])
    for nombre in ("Extraida", "Recibida", "Analizada"):
        _estado(db, nombre)
    db.flush()
    nacimiento = hoy - timedelta(days=730)
    mascotas = [
        Mascota(nombre=f"Mascota {i} G4", fecha_nacimiento=nacimiento,
                responsable=cliente, especie=especie,
                historia_clinica=HistoriaClinica(numero=9500 + i))
        for i in (1, 2, 3, 4)
    ]
    db.add_all(mascotas)
    db.flush()
    mascotas[0].historia_clinica.registrar_vacunacion(rabia, ayer)
    mascotas[3].historia_clinica.registrar_vacunacion(rabia, ayer)
    mascotas[3].historia_clinica.registrar_vacunacion(moquillo, ayer)
    mascotas[3].activo = False
    consultas = [
        ConsultaMedica(numero=i + 1, clinica=clinica, veterinario=vet, mascota=mascota,
                       fecha=ayer, complejidad=Complejidad.BAJA, costo="10.00")
        for i, (clinica, vet, mascota) in enumerate((
            (centro, vet_centro, mascotas[0]),
            (norte, vet_norte, mascotas[1]),
            (centro, vet_centro, mascotas[3]),
        ))
    ]
    db.add_all(consultas)
    db.flush()

    recibida = _estado(db, "Recibida")
    analizada = _estado(db, "Analizada")
    muestras = []
    for numero, clinica, dia_despacho, dia_recepcion, recepcion, procesos in (
        (1, centro, ayer, ayer, time(hour=9), (3600, 9000)),
        (2, norte, hoy, hoy, time(hour=8, minute=30), (3600,)),
        (3, centro, viejo, viejo, time(hour=9), (7200,)),
    ):
        fecha_despacho = datetime.combine(dia_despacho, time(hour=8))
        contenedor = ContenedorEnvio(numero=numero)
        db.add(contenedor)
        db.flush()
        db.add(RemitoBiologico(
            numero=numero,
            fecha_emision=fecha_despacho - timedelta(hours=1),
            clinica_origen=clinica,
            laboratorio_destino="Laboratorio G4",
            estado=EstadoRemito.DESPACHADO,
            fecha_hora_despacho=fecha_despacho,
            fecha_hora_recepcion=datetime.combine(dia_recepcion, recepcion),
            contenedor=contenedor,
        ))
        base = datetime.combine(dia_recepcion, time(hour=9))
        for segundos in procesos:
            muestra = consultas[0].registrar_muestra(tipo, "G4")
            muestra.contenedor = contenedor
            muestras.append((muestra, segundos, base))
    db.flush()
    for muestra, segundos, base in muestras:
        muestra.estado_actual = recibida
        db.add(CambioEstado(muestra=muestra, estado=recibida, fecha_hora=base,
                            responsable="Recepción G4"))
        muestra.estado_actual = analizada
        db.add(CambioEstado(muestra=muestra, estado=analizada,
                            fecha_hora=base + timedelta(seconds=segundos),
                            responsable="Laboratorio G4"))
    db.commit()
    return {
        "ayer": ayer, "hoy": hoy,
        "centro": centro.id, "norte": norte.id,
        "inexistente": max(centro.id, norte.id) + 999,
        "mascotas": [mascota.id for mascota in mascotas],
    }


def _filtros(datos: dict, **cambios) -> FiltroReporteRequest:
    base = {"desde": datos["ayer"], "hasta": datos["hoy"]}
    base.update(cambios)
    return FiltroReporteRequest(**base)


# --- E63: vacunas pendientes --------------------------------------------------------

def test_vacunas_declara_nombres_de_sus_totales() -> None:
    assert ReporteVacunasPendientes.NOMBRES_TOTALES == (
        "mascotas_con_pendientes", "vacunas_pendientes",
    )


def test_service_vacunas_lista_solo_mascotas_con_pendientes(
    db: Session, datos: dict
) -> None:
    respuesta = ReporteService(db).vacunas_pendientes(FiltroReporteRequest())

    assert respuesta.totales == {
        "mascotas_con_pendientes": 3, "vacunas_pendientes": 5,
    }
    por_id = {fila["mascota_id"]: fila for fila in respuesta.filas}
    assert por_id[datos["mascotas"][0]]["vacunas_pendientes"] == ["Moquillo G4"]
    assert por_id[datos["mascotas"][1]]["vacunas_pendientes"] == [
        "Rabia G4", "Moquillo G4",
    ]
    assert por_id[datos["mascotas"][2]]["vacunas_pendientes"] == [
        "Rabia G4", "Moquillo G4",
    ]
    assert datos["mascotas"][3] not in por_id  # inactiva
    assert all("Opcional G4" not in fila["vacunas_pendientes"]
               for fila in respuesta.filas)


def test_service_vacunas_filtra_por_clinica(db: Session, datos: dict) -> None:
    respuesta = ReporteService(db).vacunas_pendientes(
        FiltroReporteRequest(clinica_id=datos["norte"])
    )

    assert [fila["mascota_id"] for fila in respuesta.filas] == [datos["mascotas"][1]]
    assert respuesta.totales == {
        "mascotas_con_pendientes": 1, "vacunas_pendientes": 2,
    }


def test_service_vacunas_sin_datos_devuelve_ceros(
    db: Session, datos: dict
) -> None:
    red = db.scalar(select(RedVeterinaria).limit(1))
    sin_mascotas = ClinicaVeterinaria(nombre="Sin mascotas G4", red=red)
    db.add(sin_mascotas)
    db.commit()

    respuesta = ReporteService(db).vacunas_pendientes(
        FiltroReporteRequest(clinica_id=sin_mascotas.id)
    )

    assert respuesta.filas == []
    assert respuesta.totales == {
        "mascotas_con_pendientes": 0, "vacunas_pendientes": 0,
    }


def test_http_vacunas_devuelve_200(client, datos: dict) -> None:
    respuesta = client.get(VACUNAS)

    assert respuesta.status_code == 200
    assert respuesta.json()["totales"] == {
        "mascotas_con_pendientes": 3, "vacunas_pendientes": 5,
    }


# --- E65: tiempos promedio ----------------------------------------------------------

def test_tiempos_declara_nombres_de_sus_totales() -> None:
    assert ReporteTiemposPromedio.NOMBRES_TOTALES == (TRANSITO, PROCESAMIENTO)
    assert "segundos" in TRANSITO and "segundos" in PROCESAMIENTO


def test_service_tiempos_promedios_en_segundos(db: Session, datos: dict) -> None:
    respuesta = ReporteService(db).tiempos_promedio(_filtros(datos))

    assert respuesta.totales == {
        TRANSITO: 2700.0, PROCESAMIENTO: 5400.0,
    }
    assert len(respuesta.filas) == 2
    assert {fila[TRANSITO] for fila in respuesta.filas} == {3600.0, 1800.0}


def test_service_tiempos_filtra_por_clinica(db: Session, datos: dict) -> None:
    respuesta = ReporteService(db).tiempos_promedio(
        _filtros(datos, clinica_id=datos["centro"])
    )

    assert respuesta.totales == {TRANSITO: 3600.0, PROCESAMIENTO: 6300.0}
    assert [fila["clinica"] for fila in respuesta.filas] == ["Centro G4"]


def test_service_tiempos_usa_fecha_de_despacho(
    db: Session, datos: dict
) -> None:
    """El remito viejo queda fuera aunque su tratamiento ocurra después."""
    respuesta = ReporteService(db).tiempos_promedio(
        _filtros(datos, desde=datos["hoy"], hasta=datos["hoy"])
    )

    assert respuesta.totales == {TRANSITO: 1800.0, PROCESAMIENTO: 3600.0}


def test_service_tiempos_sin_datos_devuelve_ceros(db: Session, datos: dict) -> None:
    futuro = datos["hoy"] + timedelta(days=5)
    respuesta = ReporteService(db).tiempos_promedio(
        _filtros(datos, desde=futuro, hasta=futuro + timedelta(days=2))
    )

    assert respuesta.filas == []
    assert respuesta.totales == {TRANSITO: 0.0, PROCESAMIENTO: 0.0}


def test_http_tiempos_devuelve_segundos(client, datos: dict) -> None:
    respuesta = client.get(TIEMPOS, params={
        "desde": datos["ayer"].isoformat(), "hasta": datos["hoy"].isoformat(),
    })

    assert respuesta.status_code == 200
    assert respuesta.json()["totales"] == {
        TRANSITO: 2700.0, PROCESAMIENTO: 5400.0,
    }


@pytest.mark.parametrize("ruta", [VACUNAS, TIEMPOS])
def test_http_clinica_inexistente_es_404(client, datos: dict, ruta: str) -> None:
    respuesta = client.get(ruta, params={"clinica_id": datos["inexistente"]})
    assert respuesta.status_code == 404


@pytest.mark.parametrize("ruta", [VACUNAS, TIEMPOS])
def test_http_clinica_cero_es_422(client, datos: dict, ruta: str) -> None:
    respuesta = client.get(ruta, params={"clinica_id": 0})
    assert respuesta.status_code == 422
