"""Rutas del módulo Clientes."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteActualizar, ClienteCrear, ClienteRespuesta
from app.services.cliente_service import ClienteService

router = APIRouter(prefix="/clientes")


@router.post(
    "",
    response_model=ClienteRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Clientes"],
    summary="Dar de alta un cliente",
    description=(
        "Crea un cliente activo con nombre y teléfono; ambos textos se recortan. "
        "Errores: 422 si faltan datos o superan el largo permitido."
    ),
)
def crear_cliente(datos: ClienteCrear, db: Session = Depends(get_db)) -> Cliente:
    """Da de alta un cliente."""
    return ClienteService(db).crear(datos)


@router.get(
    "",
    response_model=list[ClienteRespuesta],
    tags=["Clientes"],
    summary="Listar clientes activos",
    description=(
        "Devuelve solo clientes activos, con filtro opcional por nombre. "
        "Sin errores de dominio: una búsqueda sin resultados devuelve 200 con lista vacía."
    ),
)
def listar_clientes(
    nombre: str | None = None, db: Session = Depends(get_db)
) -> list[Cliente]:
    """Lista los clientes activos, con filtro opcional por nombre."""
    return ClienteService(db).listar(nombre)


@router.get(
    "/{cliente_id}",
    response_model=ClienteRespuesta,
    tags=["Clientes"],
    summary="Obtener un cliente por id",
    description=(
        "Devuelve un cliente activo por su id. "
        "Errores: 404 si no existe o está dado de baja; 422 si el id no es entero."
    ),
)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)) -> Cliente:
    """Devuelve un cliente por id."""
    return ClienteService(db).obtener(cliente_id)


@router.put(
    "/{cliente_id}",
    response_model=ClienteRespuesta,
    tags=["Clientes"],
    summary="Reemplazar los datos de un cliente",
    description=(
        "PUT de reemplazo total: nombre y teléfono son obligatorios. "
        "Errores: 404 si no existe o está inactivo; 422 si los datos no son válidos."
    ),
)
def actualizar_cliente(
    cliente_id: int, datos: ClienteActualizar, db: Session = Depends(get_db)
) -> Cliente:
    """Reemplaza el nombre y el teléfono de un cliente existente."""
    return ClienteService(db).actualizar(cliente_id, datos)


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Clientes"],
    summary="Dar de baja un cliente",
    description=(
        "Baja lógica: el cliente deja de aparecer en los listados. "
        "Errores: 404 si no existe; 409 si todavía tiene mascotas activas a cargo."
    ),
)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)) -> None:
    """Da de baja lógica un cliente."""
    ClienteService(db).eliminar(cliente_id)
