"""Acceso al catálogo de vacunas."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.especie import Especie
from app.models.vacuna import Vacuna


class VacunaRepository:
    """Consulta y guarda vacunas sin confirmar transacciones."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self, especie_id: int | None = None) -> list[Vacuna]:
        """Lista el catálogo, opcionalmente por especie aplicable."""
        consulta = select(Vacuna)
        if especie_id is not None:
            consulta = consulta.where(Vacuna.especies_aplicables.any(Especie.id == especie_id))
        return list(self.db.scalars(consulta.order_by(Vacuna.id)))

    def buscar(self, vacuna_id: int) -> Vacuna | None:
        """Busca una vacuna por identificador."""
        return self.db.get(Vacuna, vacuna_id)

    def buscar_por_nombre(self, nombre: str) -> Vacuna | None:
        """Busca el nombre único del catálogo."""
        return self.db.scalar(select(Vacuna).where(Vacuna.nombre == nombre))

    def guardar(self, vacuna: Vacuna) -> None:
        """Agrega la vacuna y envía los cambios a la base."""
        self.db.add(vacuna)
        self.db.flush()
