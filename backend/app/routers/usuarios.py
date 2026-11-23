"""Rutas de administración de usuarios."""
from app.core.dependencias import obtener_usuario_actual
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.dependencias import requiere_admin
from app.models.usuario import Usuario
from app.schemas.auth import UsuarioCrear, UsuarioRespuesta
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Autenticación"],
    dependencies=[Depends(obtener_usuario_actual)],)


@router.post(
    "",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un usuario",
    description=(
        "Crea un usuario con rol ADMIN o VETERINARIO. Solo ADMIN puede usarlo. "
        "Errores: 401 sin token válido; 403 si el rol es insuficiente; "
        "409 si el nombre de usuario ya existe; 422 si los datos son inválidos."
    ),
)
def crear_usuario(
    datos: UsuarioCrear,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(requiere_admin),
) -> Usuario:
    return UsuarioService(db).crear(datos)
