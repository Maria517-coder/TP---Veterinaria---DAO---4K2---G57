"""Contratos de entrada y salida del módulo Muestras y trazabilidad."""
from datetime import date, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.muestra import (
    CambioEstadoRespuesta,
    MuestraFiltros,
    MuestraRespuesta,
    ResultadoCrear,
)

NOMBRES_ESTADOS = (
    "Extraida",
    "Empaquetada",
    "EnTransito",
    "Recibida",
    "Analizada",
    "Rechazada",
)


@pytest.mark.parametrize("nombre", NOMBRES_ESTADOS)
def test_filtros_acepta_los_seis_estados_del_dominio(nombre: str) -> None:
    """El filtro estado solo admite los nombres reales del patrón State."""
    filtros = MuestraFiltros(estado=nombre)

    assert filtros.estado == nombre


def test_filtros_rechaza_un_estado_que_no_existe() -> None:
    """Un nombre inventado se corta en la validación, antes de llegar al service."""
    with pytest.raises(ValidationError, match="estado"):
        MuestraFiltros(estado="EnProceso")


def test_filtros_combina_los_cuatro_criterios_en_snake_case() -> None:
    """Los filtros son opcionales, combinables y usan los nombres decididos."""
    hoy = datetime.now().date()
    filtros = MuestraFiltros(
        estado="Recibida", clinica_id=3, contenedor_id=7, fecha=hoy
    )

    assert filtros.model_dump() == {
        "estado": "Recibida",
        "clinica_id": 3,
        "contenedor_id": 7,
        "fecha": hoy,
    }


@pytest.mark.parametrize("campo", ["clinica_id", "contenedor_id"])
def test_filtros_rechaza_ids_no_positivos(campo: str) -> None:
    """Un id de filtro menor a 1 no tiene sentido y se rechaza."""
    with pytest.raises(ValidationError, match=campo):
        MuestraFiltros(**{campo: 0})


def test_resultado_crear_recorta_espacios_y_exige_ambos_campos() -> None:
    """El texto y el responsable llegan limpios al modelo."""
    datos = ResultadoCrear(texto="  Negativo  ", responsable="  Luis  ")

    assert datos.texto == "Negativo"
    assert datos.responsable == "Luis"


@pytest.mark.parametrize(
    "datos,campo",
    [
        ({"texto": "   ", "responsable": "Luis"}, "texto"),
        ({"texto": "Negativo", "responsable": "   "}, "responsable"),
        ({"texto": "a" * 501, "responsable": "Luis"}, "texto"),
        ({"texto": "Negativo", "responsable": "a" * 101}, "responsable"),
        ({"texto": "Negativo"}, "responsable"),
        ({"responsable": "Luis"}, "texto"),
    ],
)
def test_resultado_crear_rechaza_datos_invalidos(
    datos: dict[str, str], campo: str
) -> None:
    """Faltan datos, quedan vacíos o exceden el largo permitido por el modelo."""
    with pytest.raises(ValidationError, match=campo):
        ResultadoCrear(**datos)


def test_respuesta_muestra_sale_de_atributos_y_muestra_el_nombre_del_estado() -> None:
    """La respuesta expone el nombre del State, no la clase interna."""
    hoy = datetime.now().date()
    objeto = SimpleNamespace(
        id=1,
        consulta_id=2,
        tipo_muestra_id=3,
        contenedor_id=4,
        estado=SimpleNamespace(nombre="Recibida"),
        fecha=hoy,
        resultado=None,
        fecha_resultado=None,
    )

    respuesta = MuestraRespuesta.model_validate(objeto, from_attributes=True)

    assert respuesta.model_dump() == {
        "id": 1,
        "consulta_id": 2,
        "tipo_muestra_id": 3,
        "contenedor_id": 4,
        "estado": "Recibida",
        "fecha": hoy,
        "resultado": None,
        "fecha_resultado": None,
    }


def test_respuesta_cambio_estado_expone_la_trazabilidad() -> None:
    """Cada registro del historial se serializa con su estado y responsable."""
    ahora = datetime.now()
    registro = SimpleNamespace(
        id=5,
        muestra_id=1,
        estado=SimpleNamespace(nombre="Analizada"),
        fecha_hora=ahora,
        responsable="Luis",
    )

    respuesta = CambioEstadoRespuesta.model_validate(registro, from_attributes=True)

    assert respuesta.model_dump() == {
        "id": 5,
        "muestra_id": 1,
        "estado": "Analizada",
        "fecha_hora": ahora,
        "responsable": "Luis",
    }
