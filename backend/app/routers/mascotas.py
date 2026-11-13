"""Rutas del módulo Mascotas.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.historia_clinica import HistoriaClinica
from app.models.consulta_medica import ConsultaMedica
from app.models.mascota import Mascota
from app.schemas.mascota import (
    ConsultaHistoriaRespuesta,
    HistoriaClinicaRespuesta,
    MascotaActualizar,
    MascotaCrear,
    MascotaRespuesta,
)
from app.services.mascota_service import MascotaService
from app.models.vacuna import Vacuna
from app.models.aplicacion_vacuna import AplicacionVacuna
from app.schemas.vacuna import VacunaCrear, VacunaRespuesta, VacunacionCrear, VacunacionRespuesta
from app.services.vacuna_service import VacunaService

router = APIRouter(tags=["Mascotas"])


@router.post("/vacunas", response_model=VacunaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_vacuna(datos: VacunaCrear, db: Session = Depends(get_db)) -> Vacuna:
    """E14: incorpora una vacuna al catálogo."""
    return VacunaService(db).crear(datos)


@router.get("/vacunas", response_model=list[VacunaRespuesta])
def listar_vacunas(
    especie_id: int | None = None, db: Session = Depends(get_db)
) -> list[Vacuna]:
    """E15: lista vacunas, con filtro opcional de especie."""
    return VacunaService(db).listar(especie_id)


@router.get(
    "/clientes/{cliente_id}/mascotas", response_model=list[MascotaRespuesta]
)
def listar_mascotas_de_cliente(
    cliente_id: int, db: Session = Depends(get_db)
) -> list[Mascota]:
    """E06: lista las mascotas activas de un cliente."""
    return MascotaService(db).listar_por_cliente(cliente_id)


@router.post(
    "/mascotas", response_model=MascotaRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_mascota(datos: MascotaCrear, db: Session = Depends(get_db)) -> Mascota:
    """E07: da de alta una mascota y su historia clínica."""
    return MascotaService(db).crear(datos)


@router.get("/mascotas", response_model=list[MascotaRespuesta])
def listar_mascotas(
    cliente_id: int | None = None,
    especie_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Mascota]:
    """E08: lista las mascotas activas, con filtros opcionales."""
    return MascotaService(db).listar(cliente_id, especie_id)


@router.get("/mascotas/{mascota_id}", response_model=MascotaRespuesta)
def obtener_mascota(mascota_id: int, db: Session = Depends(get_db)) -> Mascota:
    """E09: devuelve una mascota por id."""
    return MascotaService(db).obtener(mascota_id)


@router.put("/mascotas/{mascota_id}", response_model=MascotaRespuesta)
def actualizar_mascota(
    mascota_id: int, datos: MascotaActualizar, db: Session = Depends(get_db)
) -> Mascota:
    """E10: reemplaza los datos de una mascota existente."""
    return MascotaService(db).actualizar(mascota_id, datos)


@router.delete("/mascotas/{mascota_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_mascota(mascota_id: int, db: Session = Depends(get_db)) -> None:
    """E11: da de baja lógica una mascota."""
    MascotaService(db).eliminar(mascota_id)


@router.get(
    "/mascotas/{mascota_id}/historia-clinica", response_model=HistoriaClinicaRespuesta
)
def obtener_historia_clinica(
    mascota_id: int, db: Session = Depends(get_db)
) -> HistoriaClinica:
    """E12: devuelve la historia clínica de una mascota activa."""
    return MascotaService(db).obtener_historia_clinica(mascota_id)


@router.get(
    "/historias-clinicas/{historia_id}/consultas",
    response_model=list[ConsultaHistoriaRespuesta],
)
def listar_consultas_de_historia(
    historia_id: int, db: Session = Depends(get_db)
) -> list[ConsultaMedica]:
    """E13: lista las consultas de la historia clínica."""
    return MascotaService(db).listar_consultas(historia_id)


@router.post(
    "/historias-clinicas/{historia_id}/vacunaciones",
    response_model=VacunacionRespuesta, status_code=status.HTTP_201_CREATED,
)
def registrar_vacunacion(
    historia_id: int, datos: VacunacionCrear, db: Session = Depends(get_db)
) -> AplicacionVacuna:
    """E16: registra una vacuna aplicada en la historia."""
    return MascotaService(db).registrar_vacunacion(historia_id, datos)


@router.get(
    "/historias-clinicas/{historia_id}/vacunaciones",
    response_model=list[VacunacionRespuesta],
)
def listar_vacunaciones(
    historia_id: int, db: Session = Depends(get_db)
) -> list[AplicacionVacuna]:
    """E17: lista las aplicaciones de la historia."""
    return MascotaService(db).listar_vacunaciones(historia_id)


@router.get(
    "/historias-clinicas/{historia_id}/vacunas-pendientes",
    response_model=list[VacunaRespuesta],
)
def listar_vacunas_pendientes(
    historia_id: int, db: Session = Depends(get_db)
) -> list[Vacuna]:
    """E18: consulta las vacunas obligatorias pendientes."""
    return MascotaService(db).vacunas_pendientes(historia_id)
