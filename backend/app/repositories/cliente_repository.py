"""Acceso a datos de: Cliente."""
from sqlalchemy.orm import Session


class ClienteRepository:
    """Consultas y persistencia de: Cliente."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: buscar por id, listar con filtros, guardar y eliminar según haga falta.
