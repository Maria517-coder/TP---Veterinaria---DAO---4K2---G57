"""Rutas del módulo Mascotas.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
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

router = APIRouter()


@router.get(
    "/mascotas/{mascota_id}/carnet-vacunas",
    response_class=Response,
    tags=["Historia clínica y vacunas"],
    summary="Descargar el carnet de vacunas",
    description=(
        "Genera el carnet de vacunación en PDF con las dosis aplicadas y pendientes. "
        "Errores: 404 si la mascota no existe o está inactiva."
    ),
    responses={200: {"content": {"application/pdf": {"schema": {
        "type": "string", "format": "binary",
    }}}}},
)
def descargar_carnet(mascota_id: int, db: Session = Depends(get_db)) -> Response:
    """E19: descarga el carnet de vacunación en PDF."""
    contenido = MascotaService(db).obtener_carnet(mascota_id)
    return Response(
        content=contenido, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=carnet-vacunas-{mascota_id}.pdf"},
    )


@router.post(
    "/vacunas",
    response_model=VacunaRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Historia clínica y vacunas"],
    summary="Incorporar una vacuna al catálogo",
    description=(
        "Crea una vacuna con nombre único, especies aplicables y flag de obligatoria. "
        "Errores: 409 si ya existe una vacuna con ese nombre; 422 si no se indican especies."
    ),
)
def crear_vacuna(datos: VacunaCrear, db: Session = Depends(get_db)) -> Vacuna:
    """E14: incorpora una vacuna al catálogo."""
    return VacunaService(db).crear(datos)


@router.get(
    "/vacunas",
    response_model=list[VacunaRespuesta],
    tags=["Historia clínica y vacunas"],
    summary="Listar las vacunas del catálogo",
    description=(
        "Devuelve las vacunas, con filtro opcional por especie. "
        "Sin errores de dominio: sin resultados devuelve 200 con lista vacía."
    ),
)
def listar_vacunas(
    especie_id: int | None = None, db: Session = Depends(get_db)
) -> list[Vacuna]:
    """E15: lista vacunas, con filtro opcional de especie."""
    return VacunaService(db).listar(especie_id)


@router.get(
    "/clientes/{cliente_id}/mascotas",
    response_model=list[MascotaRespuesta],
    tags=["Mascotas"],
    summary="Listar las mascotas de un cliente",
    description=(
        "Devuelve las mascotas activas a cargo del cliente. "
        "Errores: 404 si el cliente no existe."
    ),
)
def listar_mascotas_de_cliente(
    cliente_id: int, db: Session = Depends(get_db)
) -> list[Mascota]:
    """E06: lista las mascotas activas de un cliente."""
    return MascotaService(db).listar_por_cliente(cliente_id)


@router.post(
    "/mascotas",
    response_model=MascotaRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Mascotas"],
    summary="Dar de alta una mascota",
    description=(
        "Crea la mascota junto con su historia clínica, cuyo número es igual al id de la mascota. "
        "El responsable debe ser un cliente activo. "
        "Errores: 404 si no existen el cliente o la especie; 422 si la fecha de nacimiento es futura."
    ),
)
def crear_mascota(datos: MascotaCrear, db: Session = Depends(get_db)) -> Mascota:
    """E07: da de alta una mascota y su historia clínica."""
    return MascotaService(db).crear(datos)


@router.get(
    "/mascotas",
    response_model=list[MascotaRespuesta],
    tags=["Mascotas"],
    summary="Listar mascotas activas",
    description=(
        "Devuelve las mascotas activas, con filtros opcionales por cliente y especie. "
        "Sin errores de dominio: sin resultados devuelve 200 con lista vacía."
    ),
)
def listar_mascotas(
    cliente_id: int | None = None,
    especie_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Mascota]:
    """E08: lista las mascotas activas, con filtros opcionales."""
    return MascotaService(db).listar(cliente_id, especie_id)


@router.get(
    "/mascotas/{mascota_id}",
    response_model=MascotaRespuesta,
    tags=["Mascotas"],
    summary="Obtener una mascota por id",
    description=(
        "Devuelve una mascota activa por su id. "
        "Errores: 404 si no existe o fue dada de baja."
    ),
)
def obtener_mascota(mascota_id: int, db: Session = Depends(get_db)) -> Mascota:
    """E09: devuelve una mascota por id."""
    return MascotaService(db).obtener(mascota_id)


@router.put(
    "/mascotas/{mascota_id}",
    response_model=MascotaRespuesta,
    tags=["Mascotas"],
    summary="Reemplazar los datos de una mascota",
    description=(
        "PUT de reemplazo total de una mascota activa. "
        "Errores: 404 si no existen la mascota, el cliente o la especie; "
        "422 si la fecha de nacimiento es futura."
    ),
)
def actualizar_mascota(
    mascota_id: int, datos: MascotaActualizar, db: Session = Depends(get_db)
) -> Mascota:
    """E10: reemplaza los datos de una mascota existente."""
    return MascotaService(db).actualizar(mascota_id, datos)


@router.delete(
    "/mascotas/{mascota_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Mascotas"],
    summary="Dar de baja una mascota",
    description=(
        "Baja lógica: la mascota deja de aparecer en los listados. "
        "Errores: 404 si no existe."
    ),
)
def eliminar_mascota(mascota_id: int, db: Session = Depends(get_db)) -> None:
    """E11: da de baja lógica una mascota."""
    MascotaService(db).eliminar(mascota_id)


@router.get(
    "/mascotas/{mascota_id}/historia-clinica",
    response_model=HistoriaClinicaRespuesta,
    tags=["Historia clínica y vacunas"],
    summary="Obtener la historia clínica de una mascota",
    description=(
        "Devuelve la historia clínica de una mascota activa. "
        "Errores: 404 si la mascota o su historia no existen."
    ),
)
def obtener_historia_clinica(
    mascota_id: int, db: Session = Depends(get_db)
) -> HistoriaClinica:
    """E12: devuelve la historia clínica de una mascota activa."""
    return MascotaService(db).obtener_historia_clinica(mascota_id)


@router.get(
    "/historias-clinicas/{historia_id}/consultas",
    response_model=list[ConsultaHistoriaRespuesta],
    tags=["Historia clínica y vacunas"],
    summary="Listar las consultas de una historia clínica",
    description=(
        "Devuelve las consultas registradas en la historia. "
        "Errores: 404 si no existe la historia clínica."
    ),
)
def listar_consultas_de_historia(
    historia_id: int, db: Session = Depends(get_db)
) -> list[ConsultaMedica]:
    """E13: lista las consultas de la historia clínica."""
    return MascotaService(db).listar_consultas(historia_id)


@router.post(
    "/historias-clinicas/{historia_id}/vacunaciones",
    response_model=VacunacionRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Historia clínica y vacunas"],
    summary="Registrar una vacunación",
    description=(
        "Registra una dosis aplicada en la historia y actualiza las vacunas pendientes. "
        "Errores: 404 si no existen la historia o la vacuna; 422 si la fecha es futura."
    ),
)
def registrar_vacunacion(
    historia_id: int, datos: VacunacionCrear, db: Session = Depends(get_db)
) -> AplicacionVacuna:
    """E16: registra una vacuna aplicada en la historia."""
    return MascotaService(db).registrar_vacunacion(historia_id, datos)


@router.get(
    "/historias-clinicas/{historia_id}/vacunaciones",
    response_model=list[VacunacionRespuesta],
    tags=["Historia clínica y vacunas"],
    summary="Listar las vacunaciones de una historia",
    description=(
        "Devuelve las dosis aplicadas registradas en la historia. "
        "Errores: 404 si no existe la historia clínica."
    ),
)
def listar_vacunaciones(
    historia_id: int, db: Session = Depends(get_db)
) -> list[AplicacionVacuna]:
    """E17: lista las aplicaciones de la historia."""
    return MascotaService(db).listar_vacunaciones(historia_id)


@router.get(
    "/historias-clinicas/{historia_id}/vacunas-pendientes",
    response_model=list[VacunaRespuesta],
    tags=["Historia clínica y vacunas"],
    summary="Consultar las vacunas pendientes",
    description=(
        "Calcula las vacunas obligatorias pendientes según la especie y las dosis ya aplicadas. "
        "Errores: 404 si no existe la historia clínica."
    ),
)
def listar_vacunas_pendientes(
    historia_id: int, db: Session = Depends(get_db)
) -> list[Vacuna]:
    """E18: consulta las vacunas obligatorias pendientes."""
    return MascotaService(db).vacunas_pendientes(historia_id)
