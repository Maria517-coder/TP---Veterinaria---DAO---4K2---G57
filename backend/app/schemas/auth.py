"""Schemas de autenticación y usuarios."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.models.usuario import RolUsuario

NombreUsuario = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
ContrasenaLogin = Annotated[str, StringConstraints(min_length=1, max_length=128)]
ContrasenaCrear = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class LoginRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"usuario": "admin", "contrasena": "admin123"},
    })

    usuario: NombreUsuario
    contrasena: ContrasenaLogin


class TokenRespuesta(BaseModel):
    token: str
    rol: str
    veterinario_id: int | None = None


class UsuarioCrear(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "nombre_usuario": "vet1",
            "contrasena": "secreta123",
            "rol": "VETERINARIO",
            "veterinario_id": 1,
        },
    })

    nombre_usuario: NombreUsuario
    contrasena: ContrasenaCrear
    rol: RolUsuario
    veterinario_id: int | None = None


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_usuario: str
    rol: str
    activo: bool
    veterinario_id: int | None = None
    veterinario_nombre: str | None = None
    clinica_id: int | None = None
    clinica_nombre: str | None = None
