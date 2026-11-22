"""Rutas del módulo Contenedores de envío."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.contenedor_envio import ContenedorEnvio
from app.models.remito_biologico import RemitoBiologico
from app.schemas.contenedor import (
    ContenedorCrear,
    ContenedorFiltros,
    ContenedorRespuesta,
    MuestraAgregar,
    RemitoGenerar,
)
from app.schemas.remito import RemitoRespuesta
from app.services.contenedor_service import ContenedorService

router = APIRouter(prefix="/contenedores")


def _respuesta(contenedor: ContenedorEnvio) -> ContenedorRespuesta:
    """Convierte el modelo a su contrato de salida, incluyendo datos derivados."""
    return ContenedorRespuesta(
        id=contenedor.id,
        numero=contenedor.numero,
        precinto_intacto=contenedor.precinto_intacto,
        remito_id=contenedor.remito.id if contenedor.remito is not None else None,
        cantidad_muestras=len(contenedor.muestras),
    )


@router.post(
    "",
    response_model=ContenedorRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Contenedores"],
    summary="Dar de alta un contenedor",
    description=(
        "Crea un contenedor con número correlativo y precinto intacto; el alta no "
        "necesita datos. Sin errores de dominio."
    ),
)
def crear_contenedor(
    datos: ContenedorCrear, db: Session = Depends(get_db)
) -> ContenedorRespuesta:
    """E48: da de alta un contenedor con precinto intacto (201)."""
    return _respuesta(ContenedorService(db).crear(datos))


@router.get(
    "",
    response_model=list[ContenedorRespuesta],
    tags=["Contenedores"],
    summary="Listar contenedores",
    description=(
        "Lista contenedores con filtros opcionales por remito y rango de fechas. "
        "Errores: 422 si el rango de fechas no es válido."
    ),
)
def listar_contenedores(
    filtros: Annotated[ContenedorFiltros, Query()], db: Session = Depends(get_db)
) -> list[ContenedorRespuesta]:
    """E49: lista contenedores con filtros de remito y fechas (200)."""
    return [_respuesta(contenedor) for contenedor in ContenedorService(db).listar(filtros)]


@router.get(
    "/{id}",
    response_model=ContenedorRespuesta,
    tags=["Contenedores"],
    summary="Obtener un contenedor por id",
    description=(
        "Devuelve un contenedor por su id con el remito asociado y el conteo de muestras. "
        "Errores: 404 si no existe."
    ),
)
def obtener_contenedor(id: int, db: Session = Depends(get_db)) -> ContenedorRespuesta:
    """E50: devuelve un contenedor por su id (200, 404 si no existe)."""
    return _respuesta(ContenedorService(db).obtener(id))


@router.post(
    "/{id}/muestras",
    response_model=ContenedorRespuesta,
    tags=["Contenedores"],
    summary="Agregar una muestra al contenedor",
    description=(
        "Agrega una muestra Extraida al contenedor; todas las muestras deben ser de la "
        "misma clínica de origen y pasan a Empaquetada. "
        "Errores: 404 si no existen el contenedor o la muestra; 409 si ya se generó el "
        "remito o el precinto está roto; 422 si la muestra no está Extraida o es de otra clínica."
    ),
)
def agregar_muestra(
    id: int, datos: MuestraAgregar, db: Session = Depends(get_db)
) -> ContenedorRespuesta:
    """E51: agrega una muestra Extraida de la misma clínica (200, 409/422 si no)."""
    return _respuesta(ContenedorService(db).agregar_muestra(id, datos))


@router.post(
    "/{id}/romper-precinto",
    response_model=ContenedorRespuesta,
    tags=["Contenedores"],
    summary="Marcar el precinto como roto",
    description=(
        "Registra que el precinto llegó roto, sin vuelta atrás. "
        "Errores: 404 si no existe el contenedor; 409 si ya estaba roto o si las muestras "
        "ya fueron recepcionadas."
    ),
)
def romper_precinto(
    id: int, db: Session = Depends(get_db)
) -> ContenedorRespuesta:
    """E52: marca el precinto como roto sin vuelta atrás (200, 409 si ya están dadas)."""
    return _respuesta(ContenedorService(db).romper_precinto(id))


@router.post(
    "/{id}/remito",
    response_model=RemitoRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Contenedores"],
    summary="Generar el remito del contenedor",
    description=(
        "Genera el remito en estado GENERADO con el laboratorio destino indicado. "
        "Errores: 404 si no existe el contenedor; 409 si no tiene muestras o ya tiene "
        "remito; 422 si falta el laboratorio destino."
    ),
)
def generar_remito(
    id: int, datos: RemitoGenerar, db: Session = Depends(get_db)
) -> RemitoBiologico:
    """E53: genera el remito en GENERADO (201, 409 si no hay muestras o ya existe)."""
    return ContenedorService(db).generar_remito(id, datos)


@router.get(
    "/{id}/remito",
    response_model=RemitoRespuesta,
    tags=["Contenedores"],
    summary="Obtener el remito del contenedor",
    description=(
        "Devuelve el remito asociado al contenedor. "
        "Errores: 404 si no existe el contenedor o todavía no tiene remito."
    ),
)
def obtener_remito(id: int, db: Session = Depends(get_db)) -> RemitoBiologico:
    """E54: devuelve el remito del contenedor (200, 404 si todavía no lo tiene)."""
    return ContenedorService(db).obtener_remito(id)
