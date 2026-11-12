"""Acceso a datos de: Clínica, veterinario y tipo de muestra."""
from sqlalchemy.orm import Session


class ClinicaRepository:
    """Consultas y persistencia de: Clínica, veterinario y tipo de muestra."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: buscar por id, listar con filtros, guardar y eliminar según haga falta.
