"""Schemas de Pydantic del módulo Clientes."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Nombre = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
Telefono = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=30),
]


class ClienteCrear(BaseModel):
    """Datos de entrada para dar de alta un cliente."""

    nombre: Nombre
    telefono: Telefono


class ClienteActualizar(BaseModel):
    """Datos de entrada para reemplazar un cliente (PUT)."""

    nombre: Nombre
    telefono: Telefono


class ClienteRespuesta(BaseModel):
    """Datos de salida de un cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    telefono: str
    activo: bool
