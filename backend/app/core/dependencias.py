"""Dependencias de autenticaci?n y autorizaci?n."""
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
        raise NoAutenticado("Token inv?lido o ausente")
    datos = decodificar_token(credenciales.credentials)
    usuario_id = datos.get("id")
    if usuario_id is None:
        raise NoAutenticado("Token inv?lido o ausente")
    usuario = UsuarioService(db).obtener_por_id(int(usuario_id))
    if usuario is None or not usuario.activo:
        raise NoAutenticado("Token inv?lido o ausente")
    return usuario


def requiere_admin(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol != RolUsuario.ADMIN.value:
        raise AccesoProhibido("No ten?s permisos para realizar esta acci?n")
    return usuario


def verificar_propio(usuario: Usuario, veterinario_id: int) -> None:
    """VETERINARIO solo puede operar sobre su propio veterinario_id; ADMIN no tiene restricci?n."""
    if usuario.rol == RolUsuario.ADMIN.value:
        return
    if usuario.veterinario_id != veterinario_id:
        raise AccesoProhibido(
            "No ten?s permisos para operar sobre la agenda o consultas de otro veterinario"
        )
