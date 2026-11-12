"""Casos de uso del módulo Remitos biológicos."""
from sqlalchemy.orm import Session


class RemitoService:
    """Orquesta los casos de uso de Remitos biológicos."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
