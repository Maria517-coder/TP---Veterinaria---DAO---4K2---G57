"""Agenda de un veterinario: conjunto de sus turnos. No tiene tabla propia."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.turno import Turno


class Agenda:
    def __init__(self, turnos: list["Turno"]) -> None:
        self.turnos = turnos

    def agregar_turno(self, turno: "Turno") -> None:
        raise NotImplementedError("TODO: validar superposición y agregar el turno")

    def hay_superposicion(self, turno: "Turno") -> bool:
        raise NotImplementedError("TODO: detectar turnos que se pisan")
