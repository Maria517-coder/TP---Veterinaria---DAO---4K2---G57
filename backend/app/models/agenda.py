"""Agenda de un veterinario: conjunto de sus turnos. No tiene tabla propia."""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.exceptions import TurnoSuperpuesto

if TYPE_CHECKING:
    from app.models.turno import Turno


class Agenda:
    def __init__(self, turnos: list["Turno"]) -> None:
        self.turnos = turnos

    def agregar_turno(self, turno: "Turno") -> None:
        """Valida la superposición y agrega el turno a la agenda."""
        if self.hay_superposicion(turno):
            raise TurnoSuperpuesto("El turno se superpone con otro de la agenda")
        self.turnos.append(turno)

    def hay_superposicion(self, turno: "Turno") -> bool:
        """Indica si el turno pisa otro vigente, con intervalo semiabierto."""
        return any(
            existente.activo
            and turno.inicio < existente.fin
            and existente.inicio < turno.fin
            for existente in self.turnos
        )
