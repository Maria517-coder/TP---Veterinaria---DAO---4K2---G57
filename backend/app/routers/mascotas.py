"""Rutas del módulo Mascotas.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.mascota import Mascota
from app.schemas.mascota import MascotaActualizar, MascotaCrear, MascotaRespuesta
from app.services.mascota_service import MascotaService

router = APIRouter(tags=["Mascotas"])


@router.get(
    "/clientes/{cliente_id}/mascotas", response_model=list[MascotaRespuesta]
)
def listar_mascotas_de_cliente(
    cliente_id: int, db: Session = Depends(get_db)
) -> list[Mascota]:
    """E06: lista las mascotas activas de un cliente."""
    return MascotaService(db).listar_por_cliente(cliente_id)


@router.post(
    "/mascotas", response_model=MascotaRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_mascota(datos: MascotaCrear, db: Session = Depends(get_db)) -> Mascota:
    """E07: da de alta una mascota y su historia clínica."""
    return MascotaService(db).crear(datos)


@router.get("/mascotas", response_model=list[MascotaRespuesta])
def listar_mascotas(
    cliente_id: int | None = None,
    especie_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Mascota]:
    """E08: lista las mascotas activas, con filtros opcionales."""
    return MascotaService(db).listar(cliente_id, especie_id)


@router.get("/mascotas/{mascota_id}", response_model=MascotaRespuesta)
def obtener_mascota(mascota_id: int, db: Session = Depends(get_db)) -> Mascota:
    """E09: devuelve una mascota por id."""
    return MascotaService(db).obtener(mascota_id)


@router.put("/mascotas/{mascota_id}", response_model=MascotaRespuesta)
def actualizar_mascota(
    mascota_id: int, datos: MascotaActualizar, db: Session = Depends(get_db)
) -> Mascota:
    """E10: reemplaza los datos de una mascota existente."""
    return MascotaService(db).actualizar(mascota_id, datos)


@router.delete("/mascotas/{mascota_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_mascota(mascota_id: int, db: Session = Depends(get_db)) -> None:
    """E11: da de baja lógica una mascota."""
    MascotaService(db).eliminar(mascota_id)
