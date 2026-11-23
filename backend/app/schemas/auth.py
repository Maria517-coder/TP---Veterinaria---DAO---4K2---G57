"""Schemas de autenticación y usuarios."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.usuario import RolUsuario

NombreUsuario = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Contrasena = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class LoginRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"usuario": "admin", "contrasena": "admin123"},
    })

    usuario: NombreUsuario
    contrasena: Contrasena


class TokenRespuesta(BaseModel):
    token: str
    rol: str


class UsuarioCrear(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"nombre_usuario": "vet1", "contrasena": "secreta123", "rol": "VETERINARIO"},
    })

    nombre_usuario: NombreUsuario
    contrasena: Contrasena
    rol: RolUsuario


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_usuario: str
    rol: str
    activo: bool
