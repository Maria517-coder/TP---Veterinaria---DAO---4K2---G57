"""Acceso a datos de: Muestra biológica."""
from sqlalchemy.orm import Session


class MuestraRepository:
    """Consultas y persistencia de: Muestra biológica."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: buscar por id, listar con filtros, guardar y eliminar según haga falta.
