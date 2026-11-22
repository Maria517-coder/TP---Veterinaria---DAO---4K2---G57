"""Schemas de Pydantic del módulo Clínicas."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Nombre = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class ClinicaVeterinariaCrear(BaseModel):
    """Datos de entrada para dar de alta una clínica."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"nombre": "Clínica Central"},
    })

    nombre: Nombre


class ClinicaVeterinariaActualizar(BaseModel):
    """Datos de entrada para reemplazar el nombre de una clínica (PUT)."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"nombre": "Clínica Central Actualizada"},
    })

    nombre: Nombre


class ClinicaVeterinariaRespuesta(BaseModel):
    """Datos de salida de una clínica."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    red_id: int
