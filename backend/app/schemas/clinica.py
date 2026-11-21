"""Schemas de Pydantic del módulo Clínicas."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Nombre = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class ClinicaVeterinariaCrear(BaseModel):
    """Datos de entrada para dar de alta una clínica."""

    nombre: Nombre


class ClinicaVeterinariaActualizar(BaseModel):
    """Datos de entrada para reemplazar el nombre de una clínica (PUT)."""

    nombre: Nombre


class ClinicaVeterinariaRespuesta(BaseModel):
    """Datos de salida de una clínica."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    red_id: int
