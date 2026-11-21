"""Acceso a datos de: Clínica, veterinario y tipo de muestra."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.red_veterinaria import RedVeterinaria
from app.models.tipo_muestra import TipoMuestra
from app.models.veterinario import Veterinario


class ClinicaRepository:
    """Consultas y persistencia de: Clínica, veterinario y tipo de muestra."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener_red(self) -> RedVeterinaria | None:
        """Devuelve la única red, o None si todavía no fue sembrada."""
        return self.db.scalar(select(RedVeterinaria).limit(1))

    def listar_clinicas(self) -> list[ClinicaVeterinaria]:
        """Lista todas las clínicas, ordenadas por id."""
        return list(self.db.scalars(select(ClinicaVeterinaria).order_by(ClinicaVeterinaria.id)))

    def buscar_clinica_por_id(self, clinica_id: int) -> ClinicaVeterinaria | None:
        """Devuelve la clínica con ese id, o None si no existe."""
        return self.db.get(ClinicaVeterinaria, clinica_id)

    def buscar_clinica_por_nombre(self, nombre: str) -> ClinicaVeterinaria | None:
        """Devuelve la clínica con ese nombre exacto, o None si no existe."""
        return self.db.scalar(
            select(ClinicaVeterinaria).where(ClinicaVeterinaria.nombre == nombre)
        )

    def buscar_veterinario_por_id(self, veterinario_id: int) -> Veterinario | None:
        """Devuelve el veterinario activo con ese id, o None si no existe."""
        return self.db.scalar(
            select(Veterinario).where(
                Veterinario.id == veterinario_id, Veterinario.activo.is_(True)
            )
        )

    def buscar_veterinario_por_matricula(self, matricula: str) -> Veterinario | None:
        """Busca por matrícula exacta, incluidos los dados de baja."""
        return self.db.scalar(
            select(Veterinario).where(Veterinario.matricula == matricula)
        )

    def listar_veterinarios_por_clinica(
        self, clinica_id: int
    ) -> list[Veterinario]:
        """Lista los veterinarios activos de una clínica, ordenados por id."""
        return list(
            self.db.scalars(
                select(Veterinario)
                .where(
                    Veterinario.clinica_id == clinica_id,
                    Veterinario.activo.is_(True),
                )
                .order_by(Veterinario.id)
            )
        )

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
