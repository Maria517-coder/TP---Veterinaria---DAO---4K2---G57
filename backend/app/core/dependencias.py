"""Dependencias de autenticación y autorización."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.seguridad import decodificar_token
from app.exceptions import AccesoProhibido, NoAutenticado
from app.models.usuario import RolUsuario, Usuario
from app.services.usuario_service import UsuarioService

# auto_error=False para devolver 401 con el formato {"detalle": ...}
seguridad_bearer = HTTPBearer(auto_error=False)


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(seguridad_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if credenciales is None or not credenciales.credentials:
        raise NoAutenticado("Token inválido o ausente")
    datos = decodificar_token(credenciales.credentials)
    usuario_id = datos.get("id")
    if usuario_id is None:
        raise NoAutenticado("Token inválido o ausente")
    usuario = UsuarioService(db).obtener_por_id(int(usuario_id))
    if usuario is None or not usuario.activo:
        raise NoAutenticado("Token inválido o ausente")
    return usuario


def requiere_admin(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol != RolUsuario.ADMIN.value:
        raise AccesoProhibido("No tenés permisos para realizar esta acción")
    return usuario
