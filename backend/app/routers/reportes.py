"""Rutas del módulo Reportes."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.reporte import FiltroReporteRequest, ReporteRespuesta
from app.services.reporte_service import ReporteService

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/facturacion", response_model=ReporteRespuesta)
def facturacion_desglosada(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E64: facturación desglosada por clínica y laboratorio."""
    return ReporteService(db).facturacion_desglosada(filtros)


@router.get("/atenciones-derivaciones", response_model=ReporteRespuesta)
def atenciones_derivaciones(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E61: atenciones clínicas y derivaciones del período."""
    return ReporteService(db).atenciones_derivaciones(filtros)


@router.get("/muestras-rechazadas", response_model=ReporteRespuesta)
def muestras_rechazadas(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E62: muestras rechazadas según la fecha del cambio de estado."""
    return ReporteService(db).muestras_rechazadas(filtros)


@router.get("/vacunas-pendientes", response_model=ReporteRespuesta)
def vacunas_pendientes(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E63: vacunas obligatorias pendientes, con filtro opcional de clínica."""
    return ReporteService(db).vacunas_pendientes(filtros)


@router.get("/tiempos-promedio", response_model=ReporteRespuesta)
def tiempos_promedio(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E65: promedios de tránsito y procesamiento en segundos."""
    return ReporteService(db).tiempos_promedio(filtros)
