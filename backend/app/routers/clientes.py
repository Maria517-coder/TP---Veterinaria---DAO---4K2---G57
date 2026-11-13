"""Rutas del módulo Clientes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteActualizar, ClienteCrear, ClienteRespuesta
from app.services.cliente_service import ClienteService

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("", response_model=ClienteRespuesta, status_code=status.HTTP_201_CREATED)
def crear_cliente(datos: ClienteCrear, db: Session = Depends(get_db)) -> Cliente:
    """Da de alta un cliente."""
    return ClienteService(db).crear(datos)


@router.get("", response_model=list[ClienteRespuesta])
def listar_clientes(
    nombre: str | None = None, db: Session = Depends(get_db)
) -> list[Cliente]:
    """Lista los clientes activos, con filtro opcional por nombre."""
    return ClienteService(db).listar(nombre)


@router.get("/{cliente_id}", response_model=ClienteRespuesta)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)) -> Cliente:
    """Devuelve un cliente por id."""
    return ClienteService(db).obtener(cliente_id)


@router.put("/{cliente_id}", response_model=ClienteRespuesta)
def actualizar_cliente(
    cliente_id: int, datos: ClienteActualizar, db: Session = Depends(get_db)
) -> Cliente:
    """Reemplaza el nombre y el teléfono de un cliente existente."""
    return ClienteService(db).actualizar(cliente_id, datos)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)) -> None:
    """Da de baja lógica un cliente."""
    ClienteService(db).eliminar(cliente_id)


# TODO GET /clientes/{id}/mascotas: lo resuelve el módulo Mascotas.
