"""Schemas de Pydantic del módulo Veterinarios."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Matricula = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=30),
]
Nombre = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class VeterinarioCrear(BaseModel):
    """Datos de entrada para dar de alta un veterinario."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"matricula": "MP-1234", "nombre": "Dra. Ana Pérez"},
    })

    matricula: Matricula
    nombre: Nombre


class VeterinarioActualizar(BaseModel):
    """Datos de entrada para reemplazar un veterinario (PUT)."""

    model_config = ConfigDict(json_schema_extra={
        "example": {"matricula": "MP-1234", "nombre": "Dra. Ana Pérez"},
    })

    matricula: Matricula
    nombre: Nombre


class VeterinarioRespuesta(BaseModel):
    """Datos de salida de un veterinario."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    matricula: str
    nombre: str
    clinica_id: int
    activo: bool
