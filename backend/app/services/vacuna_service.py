"""Casos de uso del catálogo de vacunas."""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.vacuna import Vacuna
from app.repositories.mascota_repository import MascotaRepository
from app.repositories.vacuna_repository import VacunaRepository
from app.schemas.vacuna import VacunaCrear


class VacunaService:
    """Coordina el catálogo y sus transacciones."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = VacunaRepository(db)
        self.mascotas = MascotaRepository(db)

    def listar(self, especie_id: int | None = None) -> list[Vacuna]:
        """Devuelve las vacunas del catálogo."""
        return self.repository.listar(especie_id)

    def crear(self, datos: VacunaCrear) -> Vacuna:
        """Guarda la vacuna y sus especies en una transacción."""
        especies = []
        for especie_id in dict.fromkeys(datos.especies_aplicables):
            especie = self.mascotas.buscar_especie(especie_id)
            if especie is None:
                raise RecursoNoEncontrado(f"No existe la especie {especie_id}")
            especies.append(especie)
        vacuna = Vacuna(nombre=datos.nombre, obligatoria=datos.obligatoria,
                        especies_aplicables=especies)
        try:
            self.repository.guardar(vacuna)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if self.repository.buscar_por_nombre(datos.nombre) is not None:
                raise ConflictoDeRecurso(f"Ya existe la vacuna {datos.nombre}") from None
            raise
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(vacuna)
        return vacuna
