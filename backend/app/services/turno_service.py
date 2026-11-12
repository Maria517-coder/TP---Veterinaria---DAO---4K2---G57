"""Casos de uso del módulo Agenda y turnos."""
from sqlalchemy.orm import Session


class TurnoService:
    """Orquesta los casos de uso de Agenda y turnos."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
