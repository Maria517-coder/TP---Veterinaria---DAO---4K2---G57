"""Rutas del módulo Muestras y trazabilidad."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.cambio_estado import CambioEstado
from app.models.muestra_biologica import MuestraBiologica
from app.schemas.muestra import (
    CambioEstadoRespuesta,
    MuestraFiltros,
    MuestraRespuesta,
    ResultadoCrear,
)
from app.services.muestra_service import MuestraService

router = APIRouter(prefix="/muestras")


@router.get(
    "",
    response_model=list[MuestraRespuesta],
    tags=["Muestras"],
    summary="Listar muestras con filtros",
    description=(
        "Lista muestras con filtros opcionales por estado, clínica, contenedor y fecha. "
        "Sin errores de dominio: sin resultados devuelve 200 con lista vacía."
    ),
)
def listar_muestras(
    filtros: Annotated[MuestraFiltros, Query()], db: Session = Depends(get_db)
) -> list[MuestraBiologica]:
    """Lista muestras con filtros opcionales por estado, clínica, contenedor y fecha (E44)."""
    return MuestraService(db).listar(filtros)


@router.get(
    "/{id}",
    response_model=MuestraRespuesta,
    tags=["Muestras"],
    summary="Obtener una muestra por id",
    description=(
        "Devuelve una muestra por su id. "
        "Errores: 404 si no existe."
    ),
)
def obtener_muestra(id: int, db: Session = Depends(get_db)) -> MuestraBiologica:
    """Devuelve una muestra por su id (E45)."""
    return MuestraService(db).obtener_por_id(id)


@router.get(
    "/{id}/historial-estados",
    response_model=list[CambioEstadoRespuesta],
    tags=["Muestras"],
    summary="Ver el historial de estados de una muestra",
    description=(
        "Devuelve el historial inmutable de cambios de estado de la muestra. "
        "Errores: 404 si no existe."
    ),
)
def historial_estados(
    id: int, db: Session = Depends(get_db)
) -> list[CambioEstado]:
    """Devuelve el historial inmutable de cambios de estado (E46)."""
    return MuestraService(db).historial_estados(id)


@router.post(
    "/{id}/resultado",
    response_model=MuestraRespuesta,
    tags=["Muestras"],
    summary="Registrar el resultado de una muestra",
    description=(
        "Procesa una muestra Recibida, guarda el texto del resultado y la pasa a Analizada. "
        "Errores: 404 si no existe la muestra; 409 si no está Recibida o ya fue procesada; "
        "422 si faltan el texto o el responsable."
    ),
)
def registrar_resultado(
    id: int, datos: ResultadoCrear, db: Session = Depends(get_db)
) -> MuestraBiologica:
    """Procesa una muestra Recibida y devuelve el resultado ya guardado (E47)."""
    return MuestraService(db).registrar_resultado(id, datos)
