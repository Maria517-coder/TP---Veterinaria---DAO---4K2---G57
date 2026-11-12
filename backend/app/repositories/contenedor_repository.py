"""Acceso a datos de: Contenedor de envío."""
from sqlalchemy.orm import Session


class ContenedorRepository:
    """Consultas y persistencia de: Contenedor de envío."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: buscar por id, listar con filtros, guardar y eliminar según haga falta.
