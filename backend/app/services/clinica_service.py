"""Casos de uso del módulo Red y clínicas."""
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.red_veterinaria import RedVeterinaria
from app.repositories.clinica_repository import ClinicaRepository
from app.schemas.clinica import ClinicaVeterinariaActualizar, ClinicaVeterinariaCrear


class ClinicaService:
    """Orquesta los casos de uso de Red y clínicas."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ClinicaRepository(db)

    def obtener_red(self) -> RedVeterinaria:
        """E20: devuelve la red única sembrada."""
        red = self.repository.obtener_red()
        if red is None:
            raise RecursoNoEncontrado("No existe la red veterinaria")
        return red

    def agregar_clinica_a_red(self, datos: ClinicaVeterinariaCrear) -> ClinicaVeterinaria:
        """E21: agrega una clínica a la red, con nombre único."""
        self._validar_nombre_disponible(datos.nombre)
        clinica = ClinicaVeterinaria(nombre=datos.nombre)
        self.obtener_red().agregar_clinica(clinica)
        return self._persistir(clinica)

    def listar_clinicas(self) -> list[ClinicaVeterinaria]:
        """E22: devuelve todas las clínicas."""
        return self.repository.listar_clinicas()

    def obtener_clinica(self, clinica_id: int) -> ClinicaVeterinaria:
        """E23: devuelve una clínica o lanza RecursoNoEncontrado."""
        clinica = self.repository.buscar_clinica_por_id(clinica_id)
        if clinica is None:
            raise RecursoNoEncontrado(f"No existe la clínica {clinica_id}")
        return clinica

    def actualizar_clinica(
        self, clinica_id: int, datos: ClinicaVeterinariaActualizar
    ) -> ClinicaVeterinaria:
        """E24: reemplaza el nombre, sin chocar con otra clínica."""
        clinica = self.obtener_clinica(clinica_id)
        self._validar_nombre_disponible(datos.nombre, clinica.id)
        clinica.nombre = datos.nombre
        return self._persistir(clinica)

    def eliminar(self, clinica_id: int) -> None:
        """Da de baja lógica una clínica; falla si tiene veterinarios activos."""
        clinica = self.obtener_clinica(clinica_id)
        if self.repository.listar_veterinarios_por_clinica(clinica_id):
            raise ConflictoDeRecurso(
                "No se puede dar de baja una clínica con veterinarios activos"
            )
        try:
            clinica.activo = False
            self.repository.guardar(clinica)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def _validar_nombre_disponible(
        self, nombre: str, clinica_id: int | None = None
    ) -> None:
        """El nombre debe ser exactamente único; el PUT excluye su propio id."""
        existente = self.repository.buscar_clinica_por_nombre(nombre)
        if existente is not None and existente.id != clinica_id:
            raise ConflictoDeRecurso(f"Ya existe la clínica {nombre}")

    def _persistir(self, clinica: ClinicaVeterinaria) -> ClinicaVeterinaria:
        """Guarda y confirma; ante cualquier error deshace la transacción."""
        try:
            self.repository.guardar(clinica)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(clinica)
        return clinica
