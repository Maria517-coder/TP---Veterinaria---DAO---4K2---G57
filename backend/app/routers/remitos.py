"""Rutas del módulo Remitos biológicos."""
from typing import Annotated

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

router = APIRouter(prefix="/remitos", tags=["Remitos"])


def _respuesta_pdf() -> dict:
    """Documenta en OpenAPI que la respuesta es un PDF binario."""
    return {
        200: {
            "content": {
                "application/pdf": {"schema": {"type": "string", "format": "binary"}}
            }
        }
    }


@router.get("", response_model=list[RemitoRespuesta])
def listar_remitos(
    filtros: Annotated[RemitoFiltros, Query()], db: Session = Depends(get_db)
) -> list[RemitoBiologico]:
    """E55: lista remitos con filtros de estado, clínica y fechas."""
    return RemitoService(db).listar(filtros)


@router.get("/{remito_id}", response_model=RemitoRespuesta)
def obtener_remito(remito_id: int, db: Session = Depends(get_db)) -> RemitoBiologico:
    """E56: devuelve un remito por su id (404 si no existe)."""
    return RemitoService(db).obtener(remito_id)


@router.get(
    "/{remito_id}/imprimir", response_class=Response, responses=_respuesta_pdf()
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


@router.post("/{remito_id}/despachar", response_model=RemitoRespuesta)
def despachar_remito(
    remito_id: int, datos: ResponsableAccion, db: Session = Depends(get_db)
) -> RemitoBiologico:
    """E58: pasa de GENERADO a DESPACHADO (409 si el estado no permite)."""
    return RemitoService(db).despachar(remito_id, datos)


@router.post("/{remito_id}/recepcion", response_model=RemitoRespuesta)
def registrar_recepcion(
    remito_id: int, datos: ResponsableAccion, db: Session = Depends(get_db)
) -> RemitoBiologico:
    """E59: registra la recepción y devuelve el estado final del remito."""
    return RemitoService(db).recepcionar(remito_id, datos)


@router.get("/{remito_id}/tiempo-transito", response_model=TiempoTransitoRespuesta)
def tiempo_transito(
    remito_id: int, db: Session = Depends(get_db)
) -> TiempoTransitoRespuesta:
    """E60: devuelve recepción menos despacho en segundos (409 si falta alguna fecha)."""
    return TiempoTransitoRespuesta(
        tiempo_transito=RemitoService(db).tiempo_transito(remito_id)
    )
