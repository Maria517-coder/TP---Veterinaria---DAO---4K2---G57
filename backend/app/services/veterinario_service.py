"""Casos de uso del módulo Veterinarios."""
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.veterinario import Veterinario
from app.repositories.clinica_repository import ClinicaRepository
from app.schemas.veterinario import VeterinarioActualizar, VeterinarioCrear


class VeterinarioService:
    """Orquesta los casos de uso de Veterinarios."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ClinicaRepository(db)

    def crear_en_clinica(
        self, clinica_id: int, datos: VeterinarioCrear
    ) -> Veterinario:
        """E25: alta en la clínica; la Agenda no requiere persistencia propia."""
        clinica = self.repository.buscar_clinica_por_id(clinica_id)
        if clinica is None:
            raise RecursoNoEncontrado(f"No existe la clínica {clinica_id}")
        self._validar_matricula_disponible(datos.matricula)
        veterinario = Veterinario(
            clinica=clinica,
            matricula=datos.matricula,
            nombre=datos.nombre,
        )
        return self._persistir(veterinario)

    def listar_por_clinica(self, clinica_id: int) -> list[Veterinario]:
        """E26: lista los veterinarios activos de una clínica existente."""
        if self.repository.buscar_clinica_por_id(clinica_id) is None:
            raise RecursoNoEncontrado(f"No existe la clínica {clinica_id}")
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
        """E27: reemplaza matrícula y nombre, sin chocar con otro veterinario."""
        veterinario = self.obtener(veterinario_id)
        self._validar_matricula_disponible(datos.matricula, veterinario.id)
        veterinario.matricula = datos.matricula
        veterinario.nombre = datos.nombre
        return self._persistir(veterinario)

    def eliminar(self, veterinario_id: int) -> None:
        """E28: baja lógica; la matrícula sigue reservada por la columna unique."""
        veterinario = self.obtener(veterinario_id)
        veterinario.activo = False
        self._persistir(veterinario)

    def _validar_matricula_disponible(
        self, matricula: str, veterinario_id: int | None = None
    ) -> None:
        """La matrícula es exactamente única, incluso entre inactivos."""
        existente = self.repository.buscar_veterinario_por_matricula(matricula)
        if existente is not None and existente.id != veterinario_id:
            raise ConflictoDeRecurso(f"Ya existe el veterinario con matrícula {matricula}")

    def _persistir(self, veterinario: Veterinario) -> Veterinario:
        """Guarda y confirma; ante cualquier error deshace la transacción."""
        try:
            self.repository.guardar(veterinario)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(veterinario)
        return veterinario
