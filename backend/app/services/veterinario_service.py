"""Casos de uso del m?dulo Veterinarios."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.usuario import RolUsuario, Usuario
from app.models.veterinario import Veterinario
from app.repositories.clinica_repository import ClinicaRepository
from app.schemas.auth import UsuarioCrear
from app.schemas.veterinario import VeterinarioActualizar, VeterinarioCrear
from app.services.usuario_service import UsuarioService


class VeterinarioService:
    """Orquesta los casos de uso de Veterinarios."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ClinicaRepository(db)

    def crear_en_clinica(
        self, clinica_id: int, datos: VeterinarioCrear
    ) -> Veterinario:
        """E25: alta en la cl?nica; con acceso opcional crea veterinario y usuario en la misma transacci?n."""
        clinica = self.repository.buscar_clinica_por_id(clinica_id)
        if clinica is None:
            raise RecursoNoEncontrado(f"No existe la cl?nica {clinica_id}")
        self._validar_matricula_disponible(datos.matricula)
        veterinario = Veterinario(
            clinica=clinica,
            matricula=datos.matricula,
            nombre=datos.nombre,
        )
        try:
            self.repository.guardar(veterinario)
            self.db.flush()
            if datos.acceso is not None:
                UsuarioService(self.db).crear(
                    UsuarioCrear(
                        nombre_usuario=datos.acceso.nombre_usuario,
                        contrasena=datos.acceso.contrasena,
                        rol=RolUsuario.VETERINARIO,
                        veterinario_id=veterinario.id,
                    ),
                    confirmar=False,
                )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(veterinario)
        return veterinario

    def listar_por_clinica(self, clinica_id: int) -> list[Veterinario]:
        """E26: lista los veterinarios activos de una cl?nica existente."""
        if self.repository.buscar_clinica_por_id(clinica_id) is None:
            raise RecursoNoEncontrado(f"No existe la cl?nica {clinica_id}")
        return self.repository.listar_veterinarios_por_clinica(clinica_id)

    def obtener(self, veterinario_id: int) -> Veterinario:
        """Devuelve un veterinario activo o lanza RecursoNoEncontrado."""
        veterinario = self.repository.buscar_veterinario_por_id(veterinario_id)
        if veterinario is None:
            raise RecursoNoEncontrado(f"No existe el veterinario {veterinario_id}")
        return veterinario

    def actualizar(
        self, veterinario_id: int, datos: VeterinarioActualizar
    ) -> Veterinario:
        """E27: reemplaza matr?cula y nombre, sin chocar con otro veterinario."""
        veterinario = self.obtener(veterinario_id)
        self._validar_matricula_disponible(datos.matricula, veterinario.id)
        veterinario.matricula = datos.matricula
        veterinario.nombre = datos.nombre
        return self._persistir(veterinario)

    def eliminar(self, veterinario_id: int) -> None:
        """E28: baja l?gica; tambi?n desactiva el usuario vinculado para que no pueda iniciar sesi?n."""
        veterinario = self.obtener(veterinario_id)
        try:
            veterinario.activo = False
            self.repository.guardar(veterinario)
            usuario = self.db.scalar(
                select(Usuario).where(Usuario.veterinario_id == veterinario_id)
            )
            if usuario is not None:
                usuario.activo = False
                self.db.add(usuario)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def _validar_matricula_disponible(
        self, matricula: str, veterinario_id: int | None = None
    ) -> None:
        """La matr?cula es exactamente ?nica, incluso entre inactivos."""
        existente = self.repository.buscar_veterinario_por_matricula(matricula)
        if existente is not None and existente.id != veterinario_id:
            raise ConflictoDeRecurso(f"Ya existe el veterinario con matr?cula {matricula}")

    def _persistir(self, veterinario: Veterinario) -> Veterinario:
        """Guarda y confirma; ante cualquier error deshace la transacci?n."""
        try:
            self.repository.guardar(veterinario)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(veterinario)
        return veterinario
