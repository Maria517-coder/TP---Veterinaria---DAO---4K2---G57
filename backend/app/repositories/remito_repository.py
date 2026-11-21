"""Acceso a datos de: Remito biológico."""
from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.estado_remito import EstadoRemito
from app.models.remito_biologico import RemitoBiologico


class RemitoRepository:
    """Consultas y persistencia de: Remito biológico."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def siguiente_numero(self) -> int:
        """Devuelve el próximo número correlativo, sin reservarlo todavía."""
        mayor = self.db.scalar(select(func.max(RemitoBiologico.numero)))
        return (mayor or 0) + 1

    def buscar_por_id(self, remito_id: int) -> RemitoBiologico | None:
        """Busca un remito por id; devuelve None si no existe."""
        return self.db.get(RemitoBiologico, remito_id)

    def buscar_por_contenedor(self, contenedor_id: int) -> RemitoBiologico | None:
        """Devuelve el remito de un contenedor, o None si todavía no lo tiene."""
        return self.db.scalar(
            select(RemitoBiologico).where(
                RemitoBiologico.contenedor_id == contenedor_id
            )
        )

    def listar(
        self,
        *,
        estado: EstadoRemito | None = None,
        clinica_id: int | None = None,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> list[RemitoBiologico]:
        """Lista remitos por id, con filtros combinables de estado, clínica y fechas."""
        consulta = select(RemitoBiologico)
        if estado is not None:
            consulta = consulta.where(RemitoBiologico.estado == estado)
        if clinica_id is not None:
            consulta = consulta.where(RemitoBiologico.clinica_origen_id == clinica_id)
        if desde is not None:
            consulta = consulta.where(
                RemitoBiologico.fecha_emision >= datetime.combine(desde, time.min)
            )
        if hasta is not None:
            consulta = consulta.where(
                RemitoBiologico.fecha_emision <= datetime.combine(hasta, time.max)
            )
        return list(self.db.scalars(consulta.order_by(RemitoBiologico.id)))

    def guardar(self, remito: RemitoBiologico) -> RemitoBiologico:
        """Agrega o actualiza el remito en la sesión, sin confirmar la transacción."""
        self.db.add(remito)
        self.db.flush()
        return remito
