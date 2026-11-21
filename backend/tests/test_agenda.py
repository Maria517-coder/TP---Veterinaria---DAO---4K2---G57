"""Reglas puras de la Agenda: solapamiento y alta de turnos."""
from datetime import datetime, timedelta

import pytest

from app.exceptions import TurnoSuperpuesto
from app.models.agenda import Agenda
from app.models.turno import Turno


@pytest.fixture()
def ahora() -> datetime:
    """Base estable: mañana, siempre relativa al momento de ejecución."""
    return datetime.now() + timedelta(days=1)


def _turno(base: datetime, desde: int, hasta: int, activo: bool = True) -> Turno:
    """Arma un turno con minutos relativos a la base."""
    return Turno(
        inicio=base + timedelta(minutes=desde),
        fin=base + timedelta(minutes=hasta),
        activo=activo,
    )


def test_superposicion_dentro_del_rango(ahora: datetime) -> None:
    """Un turno solapado se detecta."""
    agenda = Agenda([_turno(ahora, 0, 60)])

    assert agenda.hay_superposicion(_turno(ahora, 30, 90)) is True


def test_superposicion_contiene_al_existente(ahora: datetime) -> None:
    """También choca si el turno nuevo envuelve al existente."""
    agenda = Agenda([_turno(ahora, 30, 60)])

    assert agenda.hay_superposicion(_turno(ahora, 0, 90)) is True


def test_limite_exacto_no_es_superposicion(ahora: datetime) -> None:
    """El intervalo es semiabierto [inicio, fin): 60 no pisa 0-60."""
    agenda = Agenda([_turno(ahora, 0, 60)])

    assert agenda.hay_superposicion(_turno(ahora, 60, 90)) is False
    assert agenda.hay_superposicion(_turno(ahora, -30, 0)) is False


def test_intervalo_disjunto_no_es_superposicion(ahora: datetime) -> None:
    agenda = Agenda([_turno(ahora, 0, 60)])

    assert agenda.hay_superposicion(_turno(ahora, 120, 180)) is False


def test_turno_cancelado_no_bloquea_el_horario(ahora: datetime) -> None:
    """Un turno dado de baja no ocupa la agenda."""
    agenda = Agenda([_turno(ahora, 0, 60, activo=False)])

    assert agenda.hay_superposicion(_turno(ahora, 0, 60)) is False


def test_agregar_turno_lo_incorpora_a_la_agenda(ahora: datetime) -> None:
    """El alta solo muta la lista; la persistencia la hace el service."""
    agenda = Agenda([])
    turno = _turno(ahora, 0, 60)

    agenda.agregar_turno(turno)

    assert agenda.turnos == [turno]


def test_agregar_turno_superpuesto_lanza_y_no_agrega(ahora: datetime) -> None:
    """Ante un choque se avisa y la agenda queda intacta."""
    existente = _turno(ahora, 0, 60)
    agenda = Agenda([existente])
    nuevo = _turno(ahora, 30, 90)

    with pytest.raises(TurnoSuperpuesto, match="superpone"):
        agenda.agregar_turno(nuevo)

    assert agenda.turnos == [existente]
