"""Casos de uso del módulo Clientes."""
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.cliente import Cliente
from app.repositories.cliente_repository import ClienteRepository
from app.schemas.cliente import ClienteActualizar, ClienteCrear


class ClienteService:
    """Orquesta los casos de uso de Clientes."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ClienteRepository(db)

    def crear(self, datos: ClienteCrear) -> Cliente:
        """Da de alta un cliente nuevo."""
        cliente = Cliente(nombre=datos.nombre, telefono=datos.telefono)
        return self._persistir(cliente)

    def listar(self, nombre: str | None = None) -> list[Cliente]:
        """Devuelve los clientes activos, opcionalmente filtrados por nombre."""
        return self.repository.listar(nombre)

    def obtener(self, cliente_id: int) -> Cliente:
        """Devuelve un cliente activo o lanza RecursoNoEncontrado."""
        cliente = self.repository.buscar_por_id(cliente_id)
        if cliente is None:
            raise RecursoNoEncontrado(f"No existe el cliente {cliente_id}")
        return cliente

    def actualizar(self, cliente_id: int, datos: ClienteActualizar) -> Cliente:
        """Reemplaza el nombre y el teléfono de un cliente existente."""
        cliente = self.obtener(cliente_id)
        cliente.nombre = datos.nombre
        cliente.telefono = datos.telefono
        return self._persistir(cliente)

    def eliminar(self, cliente_id: int) -> None:
        """Da de baja lógica un cliente; falla si todavía tiene mascotas."""
        cliente = self.obtener(cliente_id)
        if self.repository.tiene_mascotas(cliente_id):
            raise ConflictoDeRecurso(
                f"El cliente {cliente_id} tiene mascotas y no puede darse de baja"
            )
        cliente.activo = False
        self._persistir(cliente)

    def _persistir(self, cliente: Cliente) -> Cliente:
        """Guarda y confirma la transacción; ante cualquier error la deshace."""
        try:
            self.repository.guardar(cliente)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        self.db.refresh(cliente)
        return cliente
