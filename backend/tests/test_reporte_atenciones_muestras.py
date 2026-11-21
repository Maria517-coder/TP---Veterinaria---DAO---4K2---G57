"""E61 y E62: atenciones/derivaciones y muestras rechazadas."""
from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CambioEstado,
    Cliente,
    ClinicaVeterinaria,
    ConsultaMedica,
    Especie,
    EstadoCatalogo,
    HistoriaClinica,
    Mascota,
    RedVeterinaria,
    TipoMuestra,
    Veterinario,
)
from app.models.complejidad import Complejidad
from app.reportes.reporte_atenciones_derivaciones import ReporteAtencionesDerivaciones
from app.reportes.reporte_muestras_rechazadas import ReporteMuestrasRechazadas
from app.schemas.reporte import FiltroReporteRequest
from app.services.reporte_service import ReporteService

ATENCIONES = "/api/reportes/atenciones-derivaciones"
RECHAZADAS = "/api/reportes/muestras-rechazadas"


@pytest.fixture()
def datos(db: Session) -> dict:
    """Consultas y rechazos con fechas relativas a hoy."""
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    viejo = hoy - timedelta(days=10)
    red = db.scalar(select(RedVeterinaria).limit(1))
    if red is None:
        red = RedVeterinaria(nombre="Red G3")
        db.add(red)
        db.flush()
    centro = ClinicaVeterinaria(nombre="Centro G3", red=red)
    norte = ClinicaVeterinaria(nombre="Norte G3", red=red)
    db.add_all([centro, norte])
    db.flush()
    vet_centro = Veterinario(nombre="Ana G3", matricula="G3-1", clinica=centro)
    vet_norte = Veterinario(nombre="Luis G3", matricula="G3-2", clinica=norte)
    cliente = Cliente(nombre="Responsable G3", telefono="123")
    especie = Especie(nombre="PERRO-G3")
    tipo = TipoMuestra(nombre="SANGRE-G3", costo_analisis="3.00")
    db.add_all([vet_centro, vet_norte, cliente, especie, tipo])
    for nombre in ("Extraida", "Rechazada"):
        if db.scalar(select(EstadoCatalogo).where(EstadoCatalogo.nombre == nombre)) is None:
            db.add(EstadoCatalogo(nombre=nombre))
    db.flush()
    rechazada = db.scalar(
        select(EstadoCatalogo).where(EstadoCatalogo.nombre == "Rechazada")
    )
    nacimiento = hoy - timedelta(days=730)
    mascotas = [
        Mascota(nombre=f"Mascota {i} G3", fecha_nacimiento=nacimiento,
                responsable=cliente, especie=especie,
                historia_clinica=HistoriaClinica(numero=9400 + i))
        for i in (1, 2)
    ]
    db.add_all(mascotas)
    db.flush()
    consultas = [
        ConsultaMedica(numero=1, clinica=centro, veterinario=vet_centro,
                       mascota=mascotas[0], fecha=ayer,
                       complejidad=Complejidad.BAJA, costo="10.00"),
        ConsultaMedica(numero=2, clinica=centro, veterinario=vet_centro,
                       mascota=mascotas[0], fecha=viejo,
                       complejidad=Complejidad.BAJA, costo="10.00"),
        ConsultaMedica(numero=3, clinica=norte, veterinario=vet_norte,
                       mascota=mascotas[1], fecha=ayer,
                       complejidad=Complejidad.BAJA, costo="10.00"),
    ]
    db.add_all(consultas)
    db.flush()
    muestras = []
    for consulta in consultas:
        for _ in range(2 if consulta.numero == 1 else 1):
            muestra = consulta.registrar_muestra(tipo, "G3")
            muestras.append(muestra)
    db.flush()
    for muestra, dia in ((muestras[0], ayer), (muestras[2], viejo), (muestras[3], hoy)):
        muestra.estado_actual = rechazada
        db.add(CambioEstado(
            muestra=muestra, estado=rechazada,
            fecha_hora=datetime.combine(dia, time(hour=12)),
            responsable="Transporte G3",
        ))
    db.commit()
    return {
        "ayer": ayer, "hoy": hoy, "centro": centro.id, "norte": norte.id,
        "inexistente": max(centro.id, norte.id) + 999,
    }


def _filtros(datos: dict, **cambios) -> FiltroReporteRequest:
    base = {"desde": datos["ayer"], "hasta": datos["hoy"]}
    base.update(cambios)
    return FiltroReporteRequest(**base)


# --- E61: atenciones y derivaciones -------------------------------------------------

def test_atenciones_declara_nombres_de_sus_totales() -> None:
    assert ReporteAtencionesDerivaciones.NOMBRES_TOTALES == (
        "atenciones", "derivaciones",
    )


def test_service_atenciones_cuenta_consultas_y_derivaciones(
    db: Session, datos: dict
) -> None:
    respuesta = ReporteService(db).atenciones_derivaciones(_filtros(datos))

    assert respuesta.totales == {"atenciones": 2, "derivaciones": 2}
    assert [fila["numero"] for fila in respuesta.filas] == [1, 3]
    centro = respuesta.filas[0]
    assert centro["clinica"] == "Centro G3"
    assert centro["muestras_derivadas"] == 2
    assert respuesta.filas[1]["muestras_derivadas"] == 1


def test_service_atenciones_filtra_por_clinica(db: Session, datos: dict) -> None:
    respuesta = ReporteService(db).atenciones_derivaciones(
        _filtros(datos, clinica_id=datos["norte"])
    )

    assert [fila["clinica"] for fila in respuesta.filas] == ["Norte G3"]
    assert respuesta.totales == {"atenciones": 1, "derivaciones": 1}


def test_service_atenciones_sin_datos_devuelve_ceros(db: Session, datos: dict) -> None:
    respuesta = ReporteService(db).atenciones_derivaciones(
        _filtros(datos, desde=datos["hoy"], hasta=datos["hoy"])
    )

    assert respuesta.filas == []
    assert respuesta.totales == {"atenciones": 0, "derivaciones": 0}


def test_http_atenciones_devuelve_200(client, datos: dict) -> None:
    respuesta = client.get(ATENCIONES, params={
        "desde": datos["ayer"].isoformat(), "hasta": datos["hoy"].isoformat(),
    })

    assert respuesta.status_code == 200
    assert respuesta.json()["totales"] == {"atenciones": 2, "derivaciones": 2}


def test_http_atenciones_sin_datos_es_200(client, datos: dict) -> None:
    respuesta = client.get(ATENCIONES, params={
        "desde": (datos["hoy"] + timedelta(days=1)).isoformat(),
    })

    assert respuesta.status_code == 200
    assert respuesta.json()["filas"] == []
    assert respuesta.json()["totales"] == {"atenciones": 0, "derivaciones": 0}


# --- E62: muestras rechazadas -------------------------------------------------------

def test_rechazadas_declara_nombres_de_sus_totales() -> None:
    assert ReporteMuestrasRechazadas.NOMBRES_TOTALES == ("muestras_rechazadas",)


def test_service_rechazadas_usa_la_fecha_del_cambio(db: Session, datos: dict) -> None:
    respuesta = ReporteService(db).muestras_rechazadas(_filtros(datos))

    assert respuesta.totales == {"muestras_rechazadas": 2}
    assert [fila["fecha"] for fila in respuesta.filas] == [
        datos["ayer"], datos["hoy"],
    ]
    assert respuesta.filas[0]["responsable"] == "Transporte G3"
    assert respuesta.filas[0]["clinica"] == "Centro G3"


def test_service_rechazadas_filtra_por_clinica(db: Session, datos: dict) -> None:
    respuesta = ReporteService(db).muestras_rechazadas(
        _filtros(datos, clinica_id=datos["norte"])
    )

    assert respuesta.totales == {"muestras_rechazadas": 1}
    assert [fila["clinica"] for fila in respuesta.filas] == ["Norte G3"]


def test_service_rechazadas_sin_datos_devuelve_cero(db: Session, datos: dict) -> None:
    futuro = datos["hoy"] + timedelta(days=3)
    respuesta = ReporteService(db).muestras_rechazadas(
        _filtros(datos, desde=futuro, hasta=futuro + timedelta(days=2))
    )

    assert respuesta.filas == []
    assert respuesta.totales == {"muestras_rechazadas": 0}


def test_http_rechazadas_devuelve_200_y_filas_vacias(client, datos: dict) -> None:
    respuesta = client.get(RECHAZADAS, params={
        "desde": datos["ayer"].isoformat(), "hasta": datos["hoy"].isoformat(),
    })

    assert respuesta.status_code == 200
    assert respuesta.json()["totales"] == {"muestras_rechazadas": 2}
    vacia = client.get(RECHAZADAS, params={
        "desde": (datos["hoy"] + timedelta(days=3)).isoformat(),
    })
    assert vacia.status_code == 200
    assert vacia.json()["filas"] == []
    assert vacia.json()["totales"] == {"muestras_rechazadas": 0}


@pytest.mark.parametrize("ruta", [ATENCIONES, RECHAZADAS])
def test_http_clinica_inexistente_es_404(client, datos: dict, ruta: str) -> None:
    respuesta = client.get(ruta, params={"clinica_id": datos["inexistente"]})
    assert respuesta.status_code == 404


@pytest.mark.parametrize("ruta", [ATENCIONES, RECHAZADAS])
def test_http_rango_invertido_es_422(client, datos: dict, ruta: str) -> None:
    respuesta = client.get(ruta, params={
        "desde": datos["hoy"].isoformat(), "hasta": datos["ayer"].isoformat(),
    })
    assert respuesta.status_code == 422
