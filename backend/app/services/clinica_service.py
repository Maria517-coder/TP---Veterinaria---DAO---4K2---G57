"""Casos de uso del módulo Red, clínicas, veterinarios y tipos de muestra."""
from sqlalchemy.orm import Session


class ClinicaService:
    """Orquesta los casos de uso de Red, clínicas, veterinarios y tipos de muestra."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
