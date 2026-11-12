"""Casos de uso del módulo Clientes."""
from sqlalchemy.orm import Session


class ClienteService:
    """Orquesta los casos de uso de Clientes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # TODO: un método por caso de uso (ver docs/endpoints_veterinaria.xlsx).
