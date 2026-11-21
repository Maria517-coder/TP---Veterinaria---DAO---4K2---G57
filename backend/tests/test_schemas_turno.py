"""Validación de los schemas de turnos, con fechas relativas a ahora."""
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.turno import TurnoCrear, TurnoDisponibilidad, TurnoRespuesta


@pytest.fixture()
def ahora() -> datetime:
    return datetime.now() + timedelta(days=1)


def test_crear_acepta_intervalo_valido(ahora: datetime) -> None:
    turno = TurnoCrear(
        mascota_id=1, inicio=ahora, fin=ahora + timedelta(minutes=60)
    )

    assert turno.mascota_id == 1
    assert turno.fin > turno.inicio


def test_crear_rechaza_fin_anterior_o_igual(ahora: datetime) -> None:
    """fin debe ser estrictamente mayor que inicio (422)."""
    with pytest.raises(ValidationError):
        TurnoCrear(mascota_id=1, inicio=ahora, fin=ahora)
    with pytest.raises(ValidationError):
        TurnoCrear(
            mascota_id=1, inicio=ahora, fin=ahora - timedelta(minutes=30)
        )


def test_crear_rechaza_inicio_en_el_pasado() -> None:
    """La validación es relativa al momento de ejecución."""
    with pytest.raises(ValidationError):
        TurnoCrear(
            mascota_id=1,
            inicio=datetime.now() - timedelta(seconds=1),
            fin=datetime.now() + timedelta(minutes=30),
        )


def test_crear_rechaza_mascota_id_invalido(ahora: datetime) -> None:
    with pytest.raises(ValidationError):
        TurnoCrear(mascota_id=0, inicio=ahora, fin=ahora + timedelta(minutes=30))


def test_disponibilidad_valida_el_intervalo(ahora: datetime) -> None:
    consulta = TurnoDisponibilidad(inicio=ahora, fin=ahora + timedelta(minutes=30))

    assert consulta.fin > consulta.inicio
    with pytest.raises(ValidationError):
        TurnoDisponibilidad(inicio=ahora, fin=ahora)


def test_respuesta_desde_modelo(ahora: datetime) -> None:
    """La salida expone los campos del modelo, sin inventar ninguno."""
    from app.models.turno import Turno

    turno = Turno(
        id=5,
        veterinario_id=2,
        mascota_id=1,
        inicio=ahora,
        fin=ahora + timedelta(minutes=30),
        activo=True,
    )

    assert TurnoRespuesta.model_validate(turno).model_dump() == {
        "id": 5,
        "veterinario_id": 2,
        "mascota_id": 1,
        "inicio": ahora,
        "fin": ahora + timedelta(minutes=30),
        "activo": True,
    }
