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

router = APIRouter(prefix="/contenedores", tags=["Contenedores"])


def _respuesta(contenedor: ContenedorEnvio) -> ContenedorRespuesta:
    """Convierte el modelo a su contrato de salida, incluyendo datos derivados."""
    return ContenedorRespuesta(
        id=contenedor.id,
        numero=contenedor.numero,
        precinto_intacto=contenedor.precinto_intacto,
        remito_id=contenedor.remito.id if contenedor.remito is not None else None,
        cantidad_muestras=len(contenedor.muestras),
    )


@router.post("", response_model=ContenedorRespuesta, status_code=status.HTTP_201_CREATED)
def crear_contenedor(
    datos: ContenedorCrear, db: Session = Depends(get_db)
) -> ContenedorRespuesta:
    """E48: da de alta un contenedor con precinto intacto (201)."""
    return _respuesta(ContenedorService(db).crear(datos))


@router.get("", response_model=list[ContenedorRespuesta])
def listar_contenedores(
    filtros: Annotated[ContenedorFiltros, Query()], db: Session = Depends(get_db)
) -> list[ContenedorRespuesta]:
    """E49: lista contenedores con filtros de remito y fechas (200)."""
    return [_respuesta(contenedor) for contenedor in ContenedorService(db).listar(filtros)]


@router.get("/{id}", response_model=ContenedorRespuesta)
def obtener_contenedor(id: int, db: Session = Depends(get_db)) -> ContenedorRespuesta:
    """E50: devuelve un contenedor por su id (200, 404 si no existe)."""
    return _respuesta(ContenedorService(db).obtener(id))


@router.post("/{id}/muestras", response_model=ContenedorRespuesta)
def agregar_muestra(
    id: int, datos: MuestraAgregar, db: Session = Depends(get_db)
) -> ContenedorRespuesta:
    """E51: agrega una muestra Extraida de la misma clínica (200, 409/422 si no)."""
    return _respuesta(ContenedorService(db).agregar_muestra(id, datos))


@router.post("/{id}/romper-precinto", response_model=ContenedorRespuesta)
def romper_precinto(
    id: int, db: Session = Depends(get_db)
) -> ContenedorRespuesta:
    """E52: marca el precinto como roto sin vuelta atrás (200, 409 si ya están dadas)."""
    return _respuesta(ContenedorService(db).romper_precinto(id))


@router.post(
    "/{id}/remito", response_model=RemitoRespuesta, status_code=status.HTTP_201_CREATED
)
def generar_remito(
    id: int, datos: RemitoGenerar, db: Session = Depends(get_db)
) -> RemitoBiologico:
    """E53: genera el remito en GENERADO (201, 409 si no hay muestras o ya existe)."""
    return ContenedorService(db).generar_remito(id, datos)


@router.get("/{id}/remito", response_model=RemitoRespuesta)
def obtener_remito(id: int, db: Session = Depends(get_db)) -> RemitoBiologico:
    """E54: devuelve el remito del contenedor (200, 404 si todavía no lo tiene)."""
    return ContenedorService(db).obtener_remito(id)
