"""Schemas de Pydantic del módulo Red."""
from pydantic import BaseModel, ConfigDict


class RedVeterinariaRespuesta(BaseModel):
    """Datos de salida de la red, sin las clínicas anidadas."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
