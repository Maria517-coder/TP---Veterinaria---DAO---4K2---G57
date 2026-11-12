"""Casos de uso del módulo Muestras y trazabilidad."""
from sqlalchemy.orm import Session


class MuestraService:
    """Orquesta los casos de uso de Muestras y trazabilidad."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
