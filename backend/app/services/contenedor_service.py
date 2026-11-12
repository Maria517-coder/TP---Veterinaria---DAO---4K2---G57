"""Casos de uso del módulo Contenedores de envío."""
from sqlalchemy.orm import Session


class ContenedorService:
    """Orquesta los casos de uso de Contenedores de envío."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
