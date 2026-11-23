"""Casos de uso de autenticación y usuarios."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.seguridad import crear_token, hashear_contrasena, verificar_contrasena
from app.exceptions import ConflictoDeRecurso, NoAutenticado
from app.models.usuario import RolUsuario, Usuario
from app.schemas.auth import LoginRequest, UsuarioCrear


MENSAJE_CREDENCIALES_INVALIDAS = "Credenciales inválidas"


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def buscar_por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.nombre_usuario == nombre_usuario))

    def obtener_por_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

    def crear(self, datos: UsuarioCrear) -> Usuario:
        existente = self.buscar_por_nombre_usuario(datos.nombre_usuario)
        if existente is not None:
            raise ConflictoDeRecurso(f"Ya existe un usuario con nombre '{datos.nombre_usuario}'")
        usuario = Usuario(
            nombre_usuario=datos.nombre_usuario,
            contrasena_hash=hashear_contrasena(datos.contrasena),
            rol=datos.rol.value if isinstance(datos.rol, RolUsuario) else str(datos.rol),
            activo=True,
        )
        try:
            self.db.add(usuario)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(usuario)
        return usuario

    def login(self, datos: LoginRequest) -> dict:
        usuario = self.buscar_por_nombre_usuario(datos.usuario)
        if usuario is None or not usuario.activo:
            raise NoAutenticado(MENSAJE_CREDENCIALES_INVALIDAS)
        if not verificar_contrasena(datos.contrasena, usuario.contrasena_hash):
            raise NoAutenticado(MENSAJE_CREDENCIALES_INVALIDAS)
        token = crear_token({"id": usuario.id, "rol": usuario.rol})
        return {"token": token, "rol": usuario.rol}

    def asegurar_admin_inicial(self, contrasena: str) -> None:
        """Crea el usuario admin si no existe. Se usa al iniciar la app."""
        if self.buscar_por_nombre_usuario("admin") is not None:
            return
        usuario = Usuario(
            nombre_usuario="admin",
            contrasena_hash=hashear_contrasena(contrasena),
            rol=RolUsuario.ADMIN.value,
            activo=True,
        )
        self.db.add(usuario)
        self.db.commit()
