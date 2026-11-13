"""Acceso a datos de: Cliente."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.mascota import Mascota


class ClienteRepository:
    """Consultas y persistencia de: Cliente."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def buscar_por_id(self, cliente_id: int) -> Cliente | None:
        """Devuelve el cliente activo con ese id, o None si no existe o está dado de baja."""
        return self.db.scalar(
            select(Cliente).where(Cliente.id == cliente_id, Cliente.activo.is_(True))
        )

    def listar(self, nombre: str | None = None) -> list[Cliente]:
        """Lista los clientes activos; con `nombre`, filtra por coincidencia parcial."""
        consulta = select(Cliente).where(Cliente.activo.is_(True))
        if nombre:
            consulta = consulta.where(Cliente.nombre.ilike(f"%{nombre}%"))
        return list(self.db.scalars(consulta.order_by(Cliente.id)))

    def guardar(self, cliente: Cliente) -> Cliente:
        """Agrega o actualiza el cliente en la sesión, sin confirmar la transacción."""
        self.db.add(cliente)
        self.db.flush()
        return cliente

    def tiene_mascotas(self, cliente_id: int) -> bool:
        """Indica si el cliente tiene al menos una mascota activa."""
        return (
            self.db.scalar(
                select(Mascota.id)
                .where(Mascota.cliente_id == cliente_id, Mascota.activo.is_(True))
                .limit(1)
            )
            is not None
        )
