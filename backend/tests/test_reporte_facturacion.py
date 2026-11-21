"""E64: facturación desglosada por clínica y laboratorio."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontrado
from app.models import (
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
from app.repositories.reporte_repository import ReporteRepository
from app.reportes.reporte_facturacion_desglosada import ReporteFacturacionDesglosada
from app.schemas.reporte import FiltroReporteRequest
from app.services.reporte_service import ReporteService

RUTA = "/api/reportes/facturacion"


@pytest.fixture()
def datos(db: Session) -> dict:
    """Dos clínicas, consultas dentro y fuera de un rango relativo a hoy."""
    hoy = date.today()
    ayer = hoy - timedelta(days=1)
    red = db.scalar(select(RedVeterinaria).limit(1))
    if red is None:
        red = RedVeterinaria(nombre="Red G2")
        db.add(red)
        db.flush()
    centro = ClinicaVeterinaria(nombre="Centro G2", red=red)
    norte = ClinicaVeterinaria(nombre="Norte G2", red=red)
    db.add_all([centro, norte])
    db.flush()
    vet_centro = Veterinario(nombre="Ana G2", matricula="G2-1", clinica=centro)
    vet_norte = Veterinario(nombre="Luis G2", matricula="G2-2", clinica=norte)
    cliente = Cliente(nombre="Responsable G2", telefono="123")
    especie = Especie(nombre="PERRO-G2")
    tipo = TipoMuestra(nombre="SANGRE-G2", costo_analisis="2.00")
    db.add_all([vet_centro, vet_norte, cliente, especie, tipo])
    if db.scalar(
        select(EstadoCatalogo).where(EstadoCatalogo.nombre == "Extraida")
    ) is None:
        db.add(EstadoCatalogo(nombre="Extraida"))
    db.flush()
    nacimiento = hoy - timedelta(days=730)
    mascota_centro = Mascota(
        nombre="Luna G2", fecha_nacimiento=nacimiento, responsable=cliente,
        especie=especie, historia_clinica=HistoriaClinica(numero=9301),
    )
    mascota_norte = Mascota(
        nombre="Sol G2", fecha_nacimiento=nacimiento, responsable=cliente,
        especie=especie, historia_clinica=HistoriaClinica(numero=9302),
    )
    db.add_all([mascota_centro, mascota_norte])
    db.flush()

    consultas = [
        ConsultaMedica(numero=1, clinica=centro, veterinario=vet_centro,
                       mascota=mascota_centro, fecha=ayer,
                       complejidad=Complejidad.BAJA, costo="10.00"),
        ConsultaMedica(numero=2, clinica=centro, veterinario=vet_centro,
                       mascota=mascota_centro, fecha=hoy,
                       complejidad=Complejidad.BAJA, costo="5.00"),
        ConsultaMedica(numero=3, clinica=centro, veterinario=vet_centro,
                       mascota=mascota_centro, fecha=hoy - timedelta(days=10),
                       complejidad=Complejidad.BAJA, costo="99.00"),
        ConsultaMedica(numero=4, clinica=norte, veterinario=vet_norte,
                       mascota=mascota_norte, fecha=ayer,
                       complejidad=Complejidad.BAJA, costo="7.00"),
    ]
    db.add_all(consultas)
    db.flush()
    for consulta in consultas:
        consulta.registrar_muestra(tipo, "G2")
    db.commit()
    return {
        "ayer": ayer, "hoy": hoy, "centro": centro.id, "norte": norte.id,
        "inexistente": max(centro.id, norte.id) + 999,
    }


def _filtros(datos: dict, **cambios) -> FiltroReporteRequest:
    base = {"desde": datos["ayer"], "hasta": datos["hoy"]}
    base.update(cambios)
    return FiltroReporteRequest(**base)


def test_reporte_declara_nombres_de_sus_totales() -> None:
    """Los nombres son estables y están en el orden del contrato posicional."""
    assert ReporteFacturacionDesglosada.NOMBRES_TOTALES == (
        "atenciones", "analisis", "total",
    )


def test_repositorio_lista_clinicas_y_filtra_por_id(db: Session, datos: dict) -> None:
    """El repositorio solo consulta: no decide ni confirma."""
    repositorio = ReporteRepository(db)
    todas = repositorio.listar_clinicas()

    assert [clinica.id for clinica in todas] == [datos["centro"], datos["norte"]]
    assert repositorio.buscar_clinica_por_id(datos["norte"]).nombre == "Norte G2"
    assert repositorio.buscar_clinica_por_id(datos["inexistente"]) is None


def test_service_desglosa_atenciones_analisis_y_total(db: Session, datos: dict) -> None:
    """Cada fila y el total general respetan el rango inclusivo."""
    respuesta = ReporteService(db).facturacion_desglosada(_filtros(datos))

    assert respuesta.titulo
    por_id = {fila["clinica_id"]: fila for fila in respuesta.filas}
    centro = por_id[datos["centro"]]
    norte = por_id[datos["norte"]]
    assert (centro["atenciones"], centro["analisis"], centro["total"]) == (
        Decimal("15.00"), Decimal("4.00"), Decimal("19.00"),
    )
    assert (norte["atenciones"], norte["analisis"], norte["total"]) == (
        Decimal("7.00"), Decimal("2.00"), Decimal("9.00"),
    )
    assert respuesta.totales == {
        "atenciones": Decimal("22.00"),
        "analisis": Decimal("6.00"),
        "total": Decimal("28.00"),
    }


def test_service_filtra_por_clinica(db: Session, datos: dict) -> None:
    """Con clinica_id solo se calcula esa clínica."""
    respuesta = ReporteService(db).facturacion_desglosada(
        _filtros(datos, clinica_id=datos["centro"])
    )

    assert [fila["clinica_id"] for fila in respuesta.filas] == [datos["centro"]]
    assert respuesta.totales["total"] == Decimal("19.00")


def test_service_rango_de_un_solo_dia_incluye_ambos_limites(db: Session, datos: dict) -> None:
    """desde igual a hasta incluye las consultas de ese día."""
    respuesta = ReporteService(db).facturacion_desglosada(
        _filtros(datos, desde=datos["hoy"], hasta=datos["hoy"])
    )

    assert respuesta.totales["atenciones"] == Decimal("5.00")
    assert respuesta.totales["analisis"] == Decimal("2.00")


def test_service_sin_datos_devuelve_filas_vacias_y_ceros(db: Session, datos: dict) -> None:
    """Un período sin consultas no es un error: devuelve 200 con ceros."""
    futuro = datos["hoy"] + timedelta(days=5)
    respuesta = ReporteService(db).facturacion_desglosada(
        _filtros(datos, desde=futuro, hasta=futuro + timedelta(days=2))
    )

    assert respuesta.filas == []
    assert respuesta.totales == {
        "atenciones": Decimal("0.00"),
        "analisis": Decimal("0.00"),
        "total": Decimal("0.00"),
    }


def test_service_rechaza_clinica_inexistente(db: Session, datos: dict) -> None:
    """La existencia se valida en el service, antes de generar el reporte."""
    with pytest.raises(RecursoNoEncontrado):
        ReporteService(db).facturacion_desglosada(
            _filtros(datos, clinica_id=datos["inexistente"])
        )


def test_http_devuelve_importes_como_texto(client, datos: dict) -> None:
    """La respuesta HTTP usa el mismo contrato con Decimal serializado en texto."""
    respuesta = client.get(RUTA, params={
        "desde": datos["ayer"].isoformat(), "hasta": datos["hoy"].isoformat(),
    })

    assert respuesta.status_code == 200
    assert respuesta.json()["totales"] == {
        "atenciones": "22.00", "analisis": "6.00", "total": "28.00",
    }
    assert len(respuesta.json()["filas"]) == 2


def test_http_sin_datos_es_200_con_ceros(client, datos: dict) -> None:
    """El caso vacío también responde 200 desde la API."""
    futuro = datos["hoy"] + timedelta(days=5)
    respuesta = client.get(RUTA, params={
        "desde": futuro.isoformat(),
        "hasta": (futuro + timedelta(days=2)).isoformat(),
    })

    assert respuesta.status_code == 200
    assert respuesta.json()["filas"] == []
    assert respuesta.json()["totales"] == {
        "atenciones": "0.00", "analisis": "0.00", "total": "0.00",
    }


def test_http_clinica_inexistente_es_404(client, datos: dict) -> None:
    """El error de dominio se traduce a 404."""
    respuesta = client.get(RUTA, params={"clinica_id": datos["inexistente"]})

    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


def test_http_rango_invertido_es_422(client, datos: dict) -> None:
    """La validación del schema se traduce a 422."""
    respuesta = client.get(RUTA, params={
        "desde": datos["hoy"].isoformat(),
        "hasta": datos["ayer"].isoformat(),
    })

    assert respuesta.status_code == 422
