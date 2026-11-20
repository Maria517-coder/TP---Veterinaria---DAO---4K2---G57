"""Acceso a datos de: Clínica, veterinario y tipo de muestra."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tipo_muestra import TipoMuestra


class ClinicaRepository:
    """Consultas y persistencia de: Clínica, veterinario y tipo de muestra."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def listar_tipos_muestra(self) -> list[TipoMuestra]:
        """Lista todos los tipos de muestra, ordenados por id."""
        return list(self.db.scalars(select(TipoMuestra).order_by(TipoMuestra.id)))

    def buscar_tipo_muestra_por_id(self, tipo_id: int) -> TipoMuestra | None:
        """Devuelve el tipo con ese id, o None si no existe."""
        return self.db.get(TipoMuestra, tipo_id)

    def buscar_tipo_muestra_por_nombre(self, nombre: str) -> TipoMuestra | None:
        """Devuelve el tipo con ese nombre exacto, o None si no existe."""
        return self.db.scalar(
            select(TipoMuestra).where(TipoMuestra.nombre == nombre)
        )

    def guardar(self, entidad: object) -> object:
        """Agrega o actualiza una entidad en la sesión, sin confirmar la transacción."""
        self.db.add(entidad)
        self.db.flush()
        return entidad
