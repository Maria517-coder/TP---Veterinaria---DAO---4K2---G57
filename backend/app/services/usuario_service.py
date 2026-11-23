"""Casos de uso de autenticación y usuarios."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.seguridad import crear_token, hashear_contrasena, verificar_contrasena
from app.exceptions import ConflictoDeRecurso, NoAutenticado, RecursoNoEncontrado, ReglaDeNegocioViolada
from app.models.usuario import RolUsuario, Usuario
from app.repositories.clinica_repository import ClinicaRepository
from app.schemas.auth import LoginRequest, UsuarioCrear


MENSAJE_CREDENCIALES_INVALIDAS = "Credenciales inválidas"


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def buscar_por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.nombre_usuario == nombre_usuario))

    def obtener_por_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

    def crear(self, datos: UsuarioCrear, confirmar: bool = True) -> Usuario:
        existente = self.buscar_por_nombre_usuario(datos.nombre_usuario)
        if existente is not None:
            raise ConflictoDeRecurso(f"Ya existe un usuario con nombre '{datos.nombre_usuario}'")

        rol = datos.rol.value if isinstance(datos.rol, RolUsuario) else str(datos.rol)
        veterinario_id = datos.veterinario_id

        if rol == RolUsuario.VETERINARIO.value:
            if veterinario_id is None:
                raise ReglaDeNegocioViolada(
                    "Un usuario con rol VETERINARIO debe tener un veterinario_id asociado"
                )
            veterinario = ClinicaRepository(self.db).buscar_veterinario_por_id(veterinario_id)
            if veterinario is None:
                raise RecursoNoEncontrado(f"No existe el veterinario {veterinario_id}")
            vinculado = self.db.scalar(
                select(Usuario).where(Usuario.veterinario_id == veterinario_id)
            )
            if vinculado is not None:
                raise ConflictoDeRecurso(
                    f"El veterinario {veterinario_id} ya tiene un usuario vinculado"
                )
        elif rol == RolUsuario.ADMIN.value:
            if veterinario_id is not None:
                raise ReglaDeNegocioViolada(
                    "Un usuario con rol ADMIN no puede tener veterinario_id"
                )

        usuario = Usuario(
            nombre_usuario=datos.nombre_usuario,
            contrasena_hash=hashear_contrasena(datos.contrasena),
            rol=rol,
            activo=True,
            veterinario_id=veterinario_id,
        )
        try:
            self.db.add(usuario)
            self.db.flush()
            if confirmar:
                self.db.commit()
                self.db.refresh(usuario)
        except Exception:
            self.db.rollback()
            raise
        return usuario

    def login(self, datos: LoginRequest) -> dict:
        usuario = self.buscar_por_nombre_usuario(datos.usuario)
        if usuario is None or not usuario.activo:
            raise NoAutenticado(MENSAJE_CREDENCIALES_INVALIDAS)
        if not verificar_contrasena(datos.contrasena, usuario.contrasena_hash):
            raise NoAutenticado(MENSAJE_CREDENCIALES_INVALIDAS)
        token = crear_token(
            {"id": usuario.id, "rol": usuario.rol, "veterinario_id": usuario.veterinario_id}
        )
        return {"token": token, "rol": usuario.rol, "veterinario_id": usuario.veterinario_id}

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
