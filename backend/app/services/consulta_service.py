"""Casos de uso del módulo Consultas y derivación."""
from sqlalchemy.orm import Session


class ConsultaService:
    """Orquesta los casos de uso de Consultas y derivación."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
