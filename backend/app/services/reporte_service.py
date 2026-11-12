"""Casos de uso del módulo Reportes."""
from sqlalchemy.orm import Session


class ReporteService:
    """Orquesta los casos de uso de Reportes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
