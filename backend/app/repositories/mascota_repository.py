"""Acceso a datos de: Mascota e historia clínica."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota


class MascotaRepository:
    """Consultas y persistencia de: Mascota e historia clínica."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def buscar_por_id(self, mascota_id: int) -> Mascota | None:
        """Devuelve la mascota activa con ese id, o None si no existe o está de baja."""
        return self.db.scalar(
            select(Mascota).where(Mascota.id == mascota_id, Mascota.activo.is_(True))
        )

    def listar(
        self, cliente_id: int | None = None, especie_id: int | None = None
    ) -> list[Mascota]:
        """Lista las mascotas activas, filtradas por responsable o especie si se pide."""
        consulta = select(Mascota).where(Mascota.activo.is_(True))
        if cliente_id is not None:
            consulta = consulta.where(Mascota.cliente_id == cliente_id)
        if especie_id is not None:
            consulta = consulta.where(Mascota.especie_id == especie_id)
        return list(self.db.scalars(consulta.order_by(Mascota.id)))

    def guardar(self, mascota: Mascota) -> Mascota:
        """Agrega o actualiza la mascota en la sesión, sin confirmar la transacción."""
        self.db.add(mascota)
        self.db.flush()
        return mascota

    def guardar_historia(self, historia: HistoriaClinica) -> HistoriaClinica:
        """Agrega la historia clínica en la sesión, sin confirmar la transacción."""
        self.db.add(historia)
        self.db.flush()
        return historia

    def buscar_especie(self, especie_id: int) -> Especie | None:
        """Devuelve la especie con ese id, o None si no existe."""
        return self.db.get(Especie, especie_id)

    def buscar_historia(self, historia_id: int) -> HistoriaClinica | None:
        """Busca una historia por su identificador."""
        return self.db.get(HistoriaClinica, historia_id)
