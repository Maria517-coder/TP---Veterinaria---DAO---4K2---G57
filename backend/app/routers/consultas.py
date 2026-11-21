"""Rutas del módulo Consultas y derivación."""
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.consulta_medica import ConsultaMedica
from app.models.muestra_biologica import MuestraBiologica
from app.schemas.consulta import (
    ConsultaCrear,
    ConsultaRespuesta,
    CostoTotalRespuesta,
    MuestraCrear,
    MuestraRespuesta,
    VacunaPendienteRespuesta,
)
from app.services.consulta_service import ConsultaService

router = APIRouter(prefix="/consultas", tags=["Consultas"])


def _respuesta_pdf() -> dict:
    """Documenta en OpenAPI que la respuesta es un PDF binario."""
    return {
        200: {
            "content": {
                "application/pdf": {"schema": {"type": "string", "format": "binary"}}
            }
        }
    }


@router.post("", response_model=ConsultaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_consulta(
    datos: ConsultaCrear, db: Session = Depends(get_db)
) -> ConsultaRespuesta:
    """E36: registra una atención y avisa las vacunas obligatorias pendientes."""
    consulta, pendientes = ConsultaService(db).crear(datos)
    respuesta = ConsultaRespuesta.model_validate(consulta)
    respuesta.vacunas_pendientes = [
        VacunaPendienteRespuesta(id=vacuna.id, nombre=vacuna.nombre)
        for vacuna in pendientes
    ]
    return respuesta


@router.get("", response_model=list[ConsultaRespuesta])
def listar_consultas(
    clinica_id: int | None = None,
    fecha: date | None = None,
    mascota_id: int | None = None,
    veterinario_id: int | None = None,
    con_muestras: bool | None = None,
    db: Session = Depends(get_db),
) -> list[ConsultaMedica]:
    """E37: lista las consultas con filtros combinables."""
    return ConsultaService(db).listar(
        clinica_id, fecha, mascota_id, veterinario_id, con_muestras
    )


@router.get("/{consulta_id}", response_model=ConsultaRespuesta)
def obtener_consulta(
    consulta_id: int, db: Session = Depends(get_db)
) -> ConsultaMedica:
    """E38: devuelve una consulta por su id."""
    return ConsultaService(db).obtener(consulta_id)


@router.post(
    "/{consulta_id}/muestras",
    response_model=MuestraRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def registrar_muestra(
    consulta_id: int, datos: MuestraCrear, db: Session = Depends(get_db)
) -> MuestraBiologica:
    """E39: crea una muestra en estado Extraida."""
    return ConsultaService(db).registrar_muestra(consulta_id, datos)


@router.get("/{consulta_id}/muestras", response_model=list[MuestraRespuesta])
def listar_muestras(
    consulta_id: int, db: Session = Depends(get_db)
) -> list[MuestraBiologica]:
    """E40: lista las muestras de una consulta."""
    return ConsultaService(db).listar_muestras(consulta_id)


@router.get(
    "/{consulta_id}/orden-derivacion",
    response_class=Response,
    responses=_respuesta_pdf(),
)
def descargar_orden_derivacion(
    consulta_id: int, db: Session = Depends(get_db)
) -> Response:
    """E41: descarga la orden de derivación en PDF (409 si no hay muestras)."""
    contenido = ConsultaService(db).orden_derivacion(consulta_id)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f"attachment; filename=orden-derivacion-{consulta_id}.pdf"
            )
        },
    )


@router.get(
    "/{consulta_id}/comprobante",
    response_class=Response,
    responses=_respuesta_pdf(),
)
def descargar_comprobante(
    consulta_id: int, db: Session = Depends(get_db)
) -> Response:
    """E42: descarga el comprobante de atención en PDF."""
    contenido = ConsultaService(db).comprobante(consulta_id)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=comprobante-{consulta_id}.pdf"
        },
    )


@router.get("/{consulta_id}/costo-total", response_model=CostoTotalRespuesta)
def obtener_costo_total(
    consulta_id: int, db: Session = Depends(get_db)
) -> dict[str, Decimal]:
    """E43: devuelve consulta + análisis de muestras, como Decimal."""
    return {"costo_total": ConsultaService(db).costo_total(consulta_id)}
