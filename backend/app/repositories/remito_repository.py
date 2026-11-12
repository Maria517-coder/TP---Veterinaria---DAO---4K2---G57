"""Acceso a datos de: Remito biológico."""
from sqlalchemy.orm import Session


class RemitoRepository:
    """Consultas y persistencia de: Remito biológico."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: buscar por id, listar con filtros, guardar y eliminar según haga falta.
