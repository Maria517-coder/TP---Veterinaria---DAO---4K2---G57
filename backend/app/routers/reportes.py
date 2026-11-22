"""Rutas del módulo Reportes."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.reporte import FiltroReporteRequest, ReporteRespuesta
from app.services.reporte_service import ReporteService

router = APIRouter(prefix="/reportes")


@router.get(
    "/facturacion",
    response_model=ReporteRespuesta,
    tags=["Reportes"],
    summary="Reporte de facturación desglosada",
    description=(
        "Factura consultas y análisis de muestras por clínica y laboratorio dentro del "
        "período; los importes se serializan como texto. "
        "Errores: 404 si la clínica indicada no existe; 422 si el rango de fechas o el "
        "id de clínica son inválidos."
    ),
)
def facturacion_desglosada(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E64: facturación desglosada por clínica y laboratorio."""
    return ReporteService(db).facturacion_desglosada(filtros)


@router.get(
    "/atenciones-derivaciones",
    response_model=ReporteRespuesta,
    tags=["Reportes"],
    summary="Reporte de atenciones y derivaciones",
    description=(
        "Cuenta las consultas y las muestras derivadas por clínica en el período. "
        "Errores: 404 si la clínica indicada no existe; 422 si el rango de fechas o el "
        "id de clínica son inválidos."
    ),
)
def atenciones_derivaciones(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E61: atenciones clínicas y derivaciones del período."""
    return ReporteService(db).atenciones_derivaciones(filtros)


@router.get(
    "/muestras-rechazadas",
    response_model=ReporteRespuesta,
    tags=["Reportes"],
    summary="Reporte de muestras rechazadas",
    description=(
        "Lista las muestras rechazadas según la fecha del cambio de estado a Rechazada. "
        "Errores: 404 si la clínica indicada no existe; 422 si el rango de fechas o el "
        "id de clínica son inválidos."
    ),
)
def muestras_rechazadas(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E62: muestras rechazadas según la fecha del cambio de estado."""
    return ReporteService(db).muestras_rechazadas(filtros)


@router.get(
    "/vacunas-pendientes",
    response_model=ReporteRespuesta,
    tags=["Reportes"],
    summary="Reporte de vacunas pendientes",
    description=(
        "Lista las vacunas obligatorias pendientes por mascota, con filtro opcional "
        "de clínica. "
        "Errores: 404 si la clínica indicada no existe; 422 si el id de clínica o el "
        "rango de fechas son inválidos."
    ),
)
def vacunas_pendientes(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E63: vacunas obligatorias pendientes, con filtro opcional de clínica."""
    return ReporteService(db).vacunas_pendientes(filtros)


@router.get(
    "/tiempos-promedio",
    response_model=ReporteRespuesta,
    tags=["Reportes"],
    summary="Reporte de tiempos promedio",
    description=(
        "Promedia en segundos el tránsito por remito y el procesamiento por muestra, "
        "filtrando los remitos por su fecha de despacho. "
        "Errores: 404 si la clínica indicada no existe; 422 si el rango de fechas o el "
        "id de clínica son inválidos."
    ),
)
def tiempos_promedio(
    filtros: Annotated[FiltroReporteRequest, Query()],
    db: Session = Depends(get_db),
) -> ReporteRespuesta:
    """E65: promedios de tránsito y procesamiento en segundos."""
    return ReporteService(db).tiempos_promedio(filtros)
