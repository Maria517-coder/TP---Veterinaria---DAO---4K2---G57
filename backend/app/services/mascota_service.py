"""Casos de uso del módulo Mascotas, historia clínica y vacunas."""
from sqlalchemy.orm import Session


class MascotaService:
    """Orquesta los casos de uso de Mascotas, historia clínica y vacunas."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
