"""Rutas del m?dulo Agenda y turnos.
Este m?dulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from datetime import date
from typing import Annotated

from app.core.dependencias import obtener_usuario_actual, verificar_propio
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.schemas.turno import TurnoCrear, TurnoDisponibilidad, TurnoRespuesta
from app.services.turno_service import TurnoService

router = APIRouter(dependencies=[Depends(obtener_usuario_actual)])


@router.post(
    "/veterinarios/{id}/turnos",
    response_model=TurnoRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Turnos y agenda"],
    summary="Reservar un turno",
    description=(
        "Reserva un turno en la agenda del veterinario; los turnos de un mismo "
        "veterinario no pueden superponerse. "
        "Errores: 404 si no existen el veterinario o la mascota; 409 si el intervalo "
        "choca con otro turno; 422 si el fin no es posterior al inicio."
    ),
)
def crear_turno(
    id: int,
    datos: TurnoCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Turno:
    """Reserva un turno en la agenda del veterinario (E32)."""
    verificar_propio(usuario, id)
    return TurnoService(db).crear(id, datos)


@router.get(
    "/veterinarios/{id}/agenda",
    response_model=list[TurnoRespuesta],
    tags=["Turnos y agenda"],
    summary="Listar la agenda de un veterinario",
    description=(
        "Lista los turnos vigentes del veterinario, con filtro opcional por fecha. "
        "Errores: 404 si no existe el veterinario."
    ),
)
def listar_agenda(
    id: int,
    fecha: date | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> list[Turno]:
    """Lista los turnos vigentes del veterinario, con filtro opcional por fecha (E33)."""
    verificar_propio(usuario, id)
    return TurnoService(db).listar_agenda(id, fecha)


@router.get(
    "/veterinarios/{id}/turnos/disponibilidad",
    tags=["Turnos y agenda"],
    summary="Consultar disponibilidad de un intervalo",
    description=(
        "Indica si el intervalo est? libre antes de reservar, sin crear el turno. "
        "Errores: 404 si no existe el veterinario; 422 si el rango de fechas es inv?lido."
    ),
)
def consultar_disponibilidad(
    id: int,
    datos: Annotated[TurnoDisponibilidad, Query()],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> dict[str, bool]:
    """Indica si el intervalo est? libre antes de reservar (E34)."""
    verificar_propio(usuario, id)
    disponible = TurnoService(db).consultar_disponibilidad(id, datos)
    return {"disponible": disponible}


@router.delete(
    "/turnos/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Turnos y agenda"],
    summary="Cancelar un turno",
    description=(
        "Cancela un turno con baja l?gica: deja de contar para la agenda. "
        "Errores: 404 si no existe el turno."
    ),
)
def cancelar_turno(
    id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> None:
    """Cancela un turno con baja l?gica (E35)."""
    turno = TurnoService(db).repository.buscar_por_id(id)
    if turno is None:
        from app.exceptions import RecursoNoEncontrado
        raise RecursoNoEncontrado(f"No existe el turno {id}")
    verificar_propio(usuario, turno.veterinario_id)
    TurnoService(db).cancelar(id)
