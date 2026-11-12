"""Acceso a datos de: Consulta médica."""
from sqlalchemy.orm import Session


class ConsultaRepository:
    """Consultas y persistencia de: Consulta médica."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: buscar por id, listar con filtros, guardar y eliminar según haga falta.
