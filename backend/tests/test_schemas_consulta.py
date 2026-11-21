"""Validación de los schemas de consultas, con fechas relativas a ahora."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.complejidad import Complejidad
from app.models.consulta_medica import ConsultaMedica
from app.models.estados import Extraida
from app.schemas.consulta import (
    ConsultaCrear,
    ConsultaRespuesta,
    CostoTotalRespuesta,
    MuestraCrear,
    MuestraRespuesta,
    VacunaPendienteRespuesta,
)


@pytest.fixture()
def hoy():
    return datetime.now().date()


def _datos(hoy, **cambios):
    base = {
        "veterinario_id": 1,
        "mascota_id": 2,
        "fecha": hoy - timedelta(days=1),
        "complejidad": Complejidad.BAJA,
        "costo": "100.00",
    }
    base.update(cambios)
    return base


def test_crear_acepta_datos_validos(hoy) -> None:
    datos = ConsultaCrear(**_datos(hoy))

    assert datos.veterinario_id == 1
    assert datos.mascota_id == 2
    assert datos.costo == Decimal("100.00")
    assert datos.complejidad is Complejidad.BAJA


def test_crear_rechaza_fecha_futura(hoy) -> None:
    with pytest.raises(ValidationError):
        ConsultaCrear(**_datos(hoy, fecha=hoy + timedelta(days=1)))


def test_crear_rechaza_costo_float(hoy) -> None:
    """Mismo criterio que costo_analisis: float se rechaza con 422."""
    with pytest.raises(ValidationError):
        ConsultaCrear(**_datos(hoy, costo=100.5))


def test_crear_rechaza_costo_negativo(hoy) -> None:
    with pytest.raises(ValidationError):
        ConsultaCrear(**_datos(hoy, costo="-0.01"))


def test_crear_rechaza_campos_obligatorios(hoy) -> None:
    with pytest.raises(ValidationError):
        ConsultaCrear(mascota_id=2, fecha=hoy, complejidad=Complejidad.BAJA, costo="1.00")


def test_muestra_crear_solo_tipo(hoy) -> None:
    assert MuestraCrear(tipo_muestra_id=3).tipo_muestra_id == 3
    with pytest.raises(ValidationError):
        MuestraCrear()
    with pytest.raises(ValidationError):
        MuestraCrear(tipo_muestra_id=0)


def test_vacuna_pendiente_respuesta() -> None:
    respuesta = VacunaPendienteRespuesta(id=7, nombre="Rabia")

    assert respuesta.model_dump() == {"id": 7, "nombre": "Rabia"}


def test_respuesta_de_consulta_desde_atributos(hoy) -> None:
    consulta = ConsultaMedica(
        id=5, numero=1, clinica_id=3, veterinario_id=1, mascota_id=2,
        fecha=hoy - timedelta(days=1), complejidad=Complejidad.MEDIA, costo="100.00",
    )

    respuesta = ConsultaRespuesta.model_validate(consulta)

    assert respuesta.numero == 1
    assert respuesta.costo == Decimal("100.00")
    assert respuesta.vacunas_pendientes == []


def test_respuesta_de_muestra_toma_el_nombre_del_estado(hoy) -> None:
    muestra = MuestraRespuesta(
        id=9, consulta_id=5, tipo_muestra_id=7, estado=Extraida(),
        fecha=hoy - timedelta(days=1), resultado=None,
    )

    assert muestra.estado == "Extraida"
    assert muestra.resultado is None


def test_respuesta_de_costo_total_es_decimal() -> None:
    respuesta = CostoTotalRespuesta(costo_total="1600.00")

    assert respuesta.costo_total == Decimal("1600.00")
