"""Acceso a datos de: Mascota e historia clínica."""
from sqlalchemy.orm import Session


class MascotaRepository:
    """Consultas y persistencia de: Mascota e historia clínica."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: buscar por id, listar con filtros, guardar y eliminar según haga falta.
