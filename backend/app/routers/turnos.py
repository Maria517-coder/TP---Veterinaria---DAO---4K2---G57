"""Rutas del módulo Agenda y turnos.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.turno import Turno
from app.schemas.turno import TurnoCrear, TurnoDisponibilidad, TurnoRespuesta
from app.services.turno_service import TurnoService

router = APIRouter(tags=["Turnos"])


@router.post(
    "/veterinarios/{id}/turnos",
    response_model=TurnoRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_turno(
    id: int, datos: TurnoCrear, db: Session = Depends(get_db)
) -> Turno:
    """Reserva un turno en la agenda del veterinario (E32)."""
    return TurnoService(db).crear(id, datos)


@router.get("/veterinarios/{id}/agenda", response_model=list[TurnoRespuesta])
def listar_agenda(
    id: int, fecha: date | None = None, db: Session = Depends(get_db)
) -> list[Turno]:
    """Lista los turnos vigentes del veterinario, con filtro opcional por fecha (E33)."""
    return TurnoService(db).listar_agenda(id, fecha)


@router.get("/veterinarios/{id}/turnos/disponibilidad")
def consultar_disponibilidad(
    id: int,
    datos: Annotated[TurnoDisponibilidad, Query()],
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """Indica si el intervalo está libre antes de reservar (E34)."""
    disponible = TurnoService(db).consultar_disponibilidad(id, datos)
    return {"disponible": disponible}


@router.delete("/turnos/{id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_turno(id: int, db: Session = Depends(get_db)) -> None:
    """Cancela un turno con baja lógica (E35)."""
    TurnoService(db).cancelar(id)
