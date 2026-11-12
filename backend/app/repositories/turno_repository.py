"""Acceso a datos de: Turno."""
from sqlalchemy.orm import Session


class TurnoRepository:
    """Consultas y persistencia de: Turno."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: buscar por id, listar con filtros, guardar y eliminar según haga falta.
