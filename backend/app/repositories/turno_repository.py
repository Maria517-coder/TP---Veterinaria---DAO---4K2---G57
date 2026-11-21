"""Acceso a datos de: Turno."""
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.turno import Turno


class TurnoRepository:
    """Consultas y persistencia de: Turno."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def buscar_por_id(self, turno_id: int) -> Turno | None:
        """Devuelve el turno vigente con ese id, o None si no existe o está cancelado."""
        return self.db.scalar(
            select(Turno).where(Turno.id == turno_id, Turno.activo.is_(True))
        )

    def listar_por_veterinario(
        self, veterinario_id: int, fecha: date | None = None
    ) -> list[Turno]:
        """Lista los turnos vigentes del veterinario, ordenados por inicio.

        Con `fecha`, filtra los que empiezan ese día (límite superior exclusivo).
        """
        consulta = select(Turno).where(
            Turno.veterinario_id == veterinario_id, Turno.activo.is_(True)
        )
        if fecha is not None:
            desde = datetime.combine(fecha, time.min)
            hasta = datetime.combine(fecha + timedelta(days=1), time.min)
            consulta = consulta.where(Turno.inicio >= desde, Turno.inicio < hasta)
        return list(self.db.scalars(consulta.order_by(Turno.inicio)))

    def guardar(self, turno: Turno) -> Turno:
        """Agrega o actualiza el turno en la sesión, sin confirmar la transacción."""
        self.db.add(turno)
        self.db.flush()
        return turno
