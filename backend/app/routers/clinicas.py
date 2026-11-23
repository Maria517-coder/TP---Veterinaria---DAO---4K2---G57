"""Rutas del módulo Red, clínicas, veterinarios y tipos de muestra.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from app.core.dependencias import obtener_usuario_actual, requiere_admin
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db

# Schemas
from app.schemas.tipo_muestra import (
    TipoMuestraActualizar,
    TipoMuestraCrear,
    TipoMuestraRespuesta,
)
from app.schemas.red import RedVeterinariaRespuesta
from app.schemas.clinica import (
    ClinicaVeterinariaActualizar,
    ClinicaVeterinariaCrear,
    ClinicaVeterinariaRespuesta,
)
from app.schemas.veterinario import (
    VeterinarioActualizar,
    VeterinarioCrear,
    VeterinarioRespuesta,
)

# Services
from app.services.tipo_muestra_service import TipoMuestraService
from app.services.clinica_service import ClinicaService
from app.services.veterinario_service import VeterinarioService

# Modelos (solo para las anotaciones de retorno)
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.red_veterinaria import RedVeterinaria
from app.models.tipo_muestra import TipoMuestra
from app.models.veterinario import Veterinario

router = APIRouter(dependencies=[Depends(obtener_usuario_actual)])

# ================================
# Red y Clínicas (E20-E24)
# ================================
@router.get(
    "/red",
    response_model=RedVeterinariaRespuesta,
    tags=["Clínicas y veterinarios"],
    summary="Obtener la red veterinaria",
    description=(
        "Devuelve la red única a la que pertenecen las clínicas. "
        "Errores: 404 si la red todavía no está configurada."
    ),
)
def obtener_red(db: Session = Depends(get_db)) -> RedVeterinaria:
    """Devuelve la red única (E20)."""
    return ClinicaService(db).obtener_red()


@router.post(
    "/red/clinicas",
    dependencies=[Depends(requiere_admin)],
    response_model=ClinicaVeterinariaRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Clínicas y veterinarios"],
    summary="Agregar una clínica a la red",
    description=(
        "Crea una clínica con nombre único dentro de la red. "
        "Errores: 404 si no existe la red; 409 si el nombre ya está en uso; "
        "422 si el nombre está vacío o supera el largo permitido."
    ),
)
def agregar_clinica(
    datos: ClinicaVeterinariaCrear, db: Session = Depends(get_db)
) -> ClinicaVeterinaria:
    """Agrega una nueva clínica a la red (E21)."""
    return ClinicaService(db).agregar_clinica_a_red(datos)


@router.get(
    "/clinicas",
    response_model=list[ClinicaVeterinariaRespuesta],
    tags=["Clínicas y veterinarios"],
    summary="Listar las clínicas de la red",
    description=(
        "Devuelve todas las clínicas de la red. "
        "Sin errores de dominio: sin clínicas devuelve 200 con lista vacía."
    ),
)
def listar_clinicas(db: Session = Depends(get_db)) -> list[ClinicaVeterinaria]:
    """Lista todas las clínicas de la red (E22)."""
    return ClinicaService(db).listar_clinicas()


@router.get(
    "/clinicas/{id}",
    response_model=ClinicaVeterinariaRespuesta,
    tags=["Clínicas y veterinarios"],
    summary="Obtener una clínica por id",
    description=(
        "Devuelve el detalle de una clínica. "
        "Errores: 404 si no existe."
    ),
)
def obtener_clinica(id: int, db: Session = Depends(get_db)) -> ClinicaVeterinaria:
    """Devuelve los detalles de una clínica por su ID (E23)."""
    return ClinicaService(db).obtener_clinica(id)


@router.put(
    "/clinicas/{id}",
    dependencies=[Depends(requiere_admin)],
    response_model=ClinicaVeterinariaRespuesta,
    tags=["Clínicas y veterinarios"],
    summary="Reemplazar el nombre de una clínica",
    description=(
        "PUT de reemplazo total del nombre de la clínica. "
        "Errores: 404 si no existe; 409 si el nombre ya está en uso; "
        "422 si el nombre no es válido."
    ),
)
def actualizar_clinica(
    id: int, datos: ClinicaVeterinariaActualizar, db: Session = Depends(get_db)
) -> ClinicaVeterinaria:
    """Actualiza el nombre de una clínica (E24)."""
    return ClinicaService(db).actualizar_clinica(id, datos)


# ================================
# Veterinarios (E25-E28)
# ================================
@router.post(
    "/clinicas/{id}/veterinarios",
    dependencies=[Depends(requiere_admin)],
    response_model=VeterinarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Clínicas y veterinarios"],
    summary="Dar de alta un veterinario en una clínica",
    description=(
        "Crea un veterinario activo con matrícula única, asociado a la clínica indicada. "
        "Errores: 404 si no existe la clínica; 409 si la matrícula ya está registrada; "
        "422 si faltan datos."
    ),
)
def crear_veterinario(
    id: int, datos: VeterinarioCrear, db: Session = Depends(get_db)
) -> Veterinario:
    """Da de alta un veterinario en una clínica específica (E25)."""
    return VeterinarioService(db).crear_en_clinica(id, datos)


@router.get(
    "/clinicas/{id}/veterinarios",
    response_model=list[VeterinarioRespuesta],
    tags=["Clínicas y veterinarios"],
    summary="Listar los veterinarios de una clínica",
    description=(
        "Devuelve los veterinarios activos de la clínica. "
        "Errores: 404 si no existe la clínica."
    ),
)
def listar_veterinarios_clinica(
    id: int, db: Session = Depends(get_db)
) -> list[Veterinario]:
    """Lista los veterinarios activos de una clínica (E26)."""
    return VeterinarioService(db).listar_por_clinica(id)


@router.put(
    "/veterinarios/{id}",
    dependencies=[Depends(requiere_admin)],
    response_model=VeterinarioRespuesta,
    tags=["Clínicas y veterinarios"],
    summary="Reemplazar los datos de un veterinario",
    description=(
        "PUT de reemplazo total de nombre y matrícula. "
        "Errores: 404 si no existe; 409 si la matrícula pertenece a otro veterinario; "
        "422 si los datos no son válidos."
    ),
)
def actualizar_veterinario(
    id: int, datos: VeterinarioActualizar, db: Session = Depends(get_db)
) -> Veterinario:
    """Reemplaza los datos de un veterinario (E27)."""
    return VeterinarioService(db).actualizar(id, datos)


@router.delete(
    "/veterinarios/{id}",
    dependencies=[Depends(requiere_admin)],
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Clínicas y veterinarios"],
    summary="Dar de baja un veterinario",
    description=(
        "Baja lógica: el veterinario deja de listarse en su clínica. "
        "Errores: 404 si no existe."
    ),
)
def eliminar_veterinario(id: int, db: Session = Depends(get_db)) -> None:
    """Da de baja lógica a un veterinario (E28)."""
    VeterinarioService(db).eliminar(id)


# ================================
# Tipos de Muestra (E29-E31)
# ================================
@router.get(
    "/tipos-muestra",
    response_model=list[TipoMuestraRespuesta],
    tags=["Tipos de muestra"],
    summary="Listar los tipos de muestra",
    description=(
        "Devuelve el catálogo de tipos de muestra con su costo de análisis. "
        "Sin errores de dominio: sin tipos devuelve 200 con lista vacía."
    ),
)
def listar_tipos_muestra(db: Session = Depends(get_db)) -> list[TipoMuestra]:
    """Lista todos los tipos de muestra biológica (E29)."""
    return TipoMuestraService(db).listar()


@router.post(
    "/tipos-muestra",
    dependencies=[Depends(requiere_admin)],
    response_model=TipoMuestraRespuesta,
    status_code=status.HTTP_201_CREATED,
    tags=["Tipos de muestra"],
    summary="Crear un tipo de muestra",
    description=(
        "Crea un tipo de muestra con nombre único y costo de análisis. "
        "El importe se envía como texto con dos decimales, por ejemplo \"100.00\". "
        "Errores: 409 si el nombre ya existe; 422 si el costo es float, negativo o inválido."
    ),
)
def crear_tipo_muestra(
    datos: TipoMuestraCrear, db: Session = Depends(get_db)
) -> TipoMuestra:
    """Crea un nuevo tipo de muestra (E30)."""
    return TipoMuestraService(db).crear(datos)


@router.put(
    "/tipos-muestra/{id}",
    dependencies=[Depends(requiere_admin)],
    response_model=TipoMuestraRespuesta,
    tags=["Tipos de muestra"],
    summary="Reemplazar un tipo de muestra",
    description=(
        "PUT de reemplazo total de nombre y costo de análisis. "
        "El importe se envía como texto con dos decimales. "
        "Errores: 404 si no existe; 409 si el nombre ya está en uso; 422 si el costo es inválido."
    ),
)
def actualizar_tipo_muestra(
    id: int, datos: TipoMuestraActualizar, db: Session = Depends(get_db)
) -> TipoMuestra:
    """Actualiza un tipo de muestra existente (E31)."""
    return TipoMuestraService(db).actualizar(id, datos)
