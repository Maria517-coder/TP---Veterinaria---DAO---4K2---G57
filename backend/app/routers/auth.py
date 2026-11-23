"""Rutas de autenticación."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.dependencias import obtener_usuario_actual
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenRespuesta, UsuarioRespuesta
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/login",
    response_model=TokenRespuesta,
    summary="Iniciar sesión",
    description=(
        "Recibe usuario y contraseña y devuelve un token firmado con rol. "
        "Errores: 401 si las credenciales son inválidas o el usuario está inactivo; "
        "422 si falta algún campo."
    ),
)
def login(datos: LoginRequest, db: Session = Depends(get_db)) -> dict:
    return UsuarioService(db).login(datos)


@router.get(
    "/yo",
    response_model=UsuarioRespuesta,
    summary="Obtener el usuario actual",
    description=(
        "Devuelve los datos del usuario autenticado por el token Bearer. "
        "Errores: 401 si el token falta, es inválido o está vencido."
    ),
)
def yo(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    return usuario
