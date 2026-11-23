"""Rutas del módulo Remitos biológicos."""
from typing import Annotated

from app.core.dependencias import obtener_usuario_actual
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.remito_biologico import RemitoBiologico
from app.schemas.remito import (
    RemitoFiltros,
    RemitoRespuesta,
    ResponsableAccion,
    TiempoTransitoRespuesta,
)
from app.services.remito_service import RemitoService

router = APIRouter(prefix="/remitos",
    dependencies=[Depends(obtener_usuario_actual)],)


def _respuesta_pdf() -> dict:
    """Documenta en OpenAPI que la respuesta es un PDF binario."""
    return {
        200: {
            "content": {
                "application/pdf": {"schema": {"type": "string", "format": "binary"}}
            }
        }
    }


@router.get(
    "",
    response_model=list[RemitoRespuesta],
    tags=["Remitos"],
    summary="Listar remitos",
    description=(
        "Lista remitos con filtros opcionales de estado, clínica y fechas. "
        "Sin errores de dominio: sin resultados devuelve 200 con lista vacía."
    ),
)
def listar_remitos(
    filtros: Annotated[RemitoFiltros, Query()], db: Session = Depends(get_db)
) -> list[RemitoBiologico]:
    """E55: lista remitos con filtros de estado, clínica y fechas."""
    return RemitoService(db).listar(filtros)


@router.get(
    "/{remito_id}",
    response_model=RemitoRespuesta,
    tags=["Remitos"],
    summary="Obtener un remito por id",
    description=(
        "Devuelve un remito por su id. "
        "Errores: 404 si no existe."
    ),
)
def obtener_remito(remito_id: int, db: Session = Depends(get_db)) -> RemitoBiologico:
    """E56: devuelve un remito por su id (404 si no existe)."""
    return RemitoService(db).obtener(remito_id)


@router.get(
    "/{remito_id}/imprimir",
    response_class=Response,
    responses=_respuesta_pdf(),
    tags=["Remitos"],
    summary="Descargar el remito en PDF",
    description=(
        "Genera el remito biológico imprimible en PDF. "
        "Errores: 404 si no existe el remito."
    ),
)
def imprimir_remito(remito_id: int, db: Session = Depends(get_db)) -> Response:
    """E57: descarga el remito biológico en PDF."""
    contenido = RemitoService(db).imprimir(remito_id)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=remito-{remito_id}.pdf"
        },
    )


@router.post(
    "/{remito_id}/despachar",
    response_model=RemitoRespuesta,
    tags=["Remitos"],
    summary="Despachar un remito",
    description=(
        "Pasa el remito de GENERADO a DESPACHADO, fecha el despacho y envía sus "
        "muestras a EnTransito. "
        "Errores: 404 si no existe; 409 si el estado no permite el despacho o las "
        "muestras no están Empaquetada; 422 si falta el responsable."
    ),
)
def despachar_remito(
    remito_id: int, datos: ResponsableAccion, db: Session = Depends(get_db)
) -> RemitoBiologico:
    """E58: pasa de GENERADO a DESPACHADO (409 si el estado no permite)."""
    return RemitoService(db).despachar(remito_id, datos)


@router.post(
    "/{remito_id}/recepcion",
    response_model=RemitoRespuesta,
    tags=["Remitos"],
    summary="Registrar la recepción de un remito",
    description=(
        "Registra la recepción y devuelve el estado final del remito; si el precinto "
        "llegó roto, las muestras pasan a Rechazada. "
        "Errores: 404 si no existe; 409 si no está DESPACHADO o las muestras no están "
        "EnTransito; 422 si falta el responsable."
    ),
)
def registrar_recepcion(
    remito_id: int, datos: ResponsableAccion, db: Session = Depends(get_db)
) -> RemitoBiologico:
    """E59: registra la recepción y devuelve el estado final del remito."""
    return RemitoService(db).recepcionar(remito_id, datos)


@router.get(
    "/{remito_id}/tiempo-transito",
    response_model=TiempoTransitoRespuesta,
    tags=["Remitos"],
    summary="Calcular el tiempo de tránsito",
    description=(
        "Devuelve recepción menos despacho en segundos, calculado por el modelo. "
        "Errores: 404 si no existe el remito; 409 si falta la fecha de despacho o de recepción."
    ),
)
def tiempo_transito(
    remito_id: int, db: Session = Depends(get_db)
) -> TiempoTransitoRespuesta:
    """E60: devuelve recepción menos despacho en segundos (409 si falta alguna fecha)."""
    return TiempoTransitoRespuesta(
        tiempo_transito=RemitoService(db).tiempo_transito(remito_id)
    )
