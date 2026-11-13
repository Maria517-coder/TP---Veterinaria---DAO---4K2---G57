"""Rutas del módulo Red, clínicas, veterinarios y tipos de muestra.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.database import get_db

# Schemas
from app.schemas.tipo_muestra import TipoMuestraActualizar, TipoMuestraCrear, TipoMuestraRespuesta
from app.schemas.red import RedVeterinariaRespuesta
from app.schemas.clinica import ClinicaVeterinariaCrear, ClinicaVeterinariaActualizar, ClinicaVeterinariaRespuesta
from app.schemas.veterinario import VeterinarioCrear, VeterinarioActualizar, VeterinarioRespuesta

# Services
from app.services.tipo_muestra_service import TipoMuestraService
from app.services.clinica_service import ClinicaService
from app.services.veterinario_service import VeterinarioService

router = APIRouter(tags=["Clínicas"])

# ================================
# Red y Clínicas (E20-E24)
# ================================
@router.get("/red", response_model=RedVeterinariaRespuesta)
def obtener_red(db: Session = Depends(get_db)):
    return ClinicaService(db).obtener_red()

@router.post("/red/clinicas", response_model=ClinicaVeterinariaRespuesta, status_code=status.HTTP_201_CREATED)
def agregar_clinica(datos: ClinicaVeterinariaCrear, db: Session = Depends(get_db)):
    """Agrega una nueva clínica a la red (E21)."""
    return ClinicaService(db).agregar_clinica_a_red(datos)

@router.get("/clinicas", response_model=list[ClinicaVeterinariaRespuesta])
def listar_clinicas(db: Session = Depends(get_db)):
    """Lista todas las clínicas de la red (E22)."""
    return ClinicaService(db).listar_clinicas()

@router.get("/clinicas/{id}", response_model=ClinicaVeterinariaRespuesta)
def obtener_clinica(id: int, db: Session = Depends(get_db)):
    """Devuelve los detalles de una clínica por su ID (E23)."""
    return ClinicaService(db).obtener_clinica(id)

@router.put("/clinicas/{id}", response_model=ClinicaVeterinariaRespuesta)
def actualizar_clinica(id: int, datos: ClinicaVeterinariaActualizar, db: Session = Depends(get_db)):
    """Actualiza el nombre de una clínica (E24)."""
    return ClinicaService(db).actualizar_clinica(id, datos)


# ================================
# Veterinarios (E25-E28)
# ================================
@router.post("/clinicas/{id}/veterinarios", response_model=VeterinarioRespuesta, status_code=status.HTTP_201_CREATED)
def crear_veterinario(id: int, datos: VeterinarioCrear, db: Session = Depends(get_db)):
    """Da de alta un veterinario en una clínica específica (E25)."""
    return VeterinarioService(db).crear_en_clinica(id, datos)

@router.get("/clinicas/{id}/veterinarios", response_model=list[VeterinarioRespuesta])
def listar_veterinarios_clinica(id: int, db: Session = Depends(get_db)):
    """Lista los veterinarios activos de una clínica (E26)."""
    return VeterinarioService(db).listar_por_clinica(id)

@router.put("/veterinarios/{id}", response_model=VeterinarioRespuesta)
def actualizar_veterinario(id: int, datos: VeterinarioActualizar, db: Session = Depends(get_db)):
    """Reemplaza los datos de un veterinario (E27)."""
    return VeterinarioService(db).actualizar(id, datos)

@router.delete("/veterinarios/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_veterinario(id: int, db: Session = Depends(get_db)):
    """Da de baja lógica a un veterinario (E28)."""
    VeterinarioService(db).eliminar(id)


# ================================
# Tipos de Muestra (E29-E31)
# ================================
@router.get("/tipos-muestra", response_model=list[TipoMuestraRespuesta])
def listar_tipos_muestra(db: Session = Depends(get_db)):
    """Lista todos los tipos de muestra biológica (E29)."""
    return TipoMuestraService(db).listar()

@router.post("/tipos-muestra", response_model=TipoMuestraRespuesta, status_code=status.HTTP_201_CREATED)
def crear_tipo_muestra(datos: TipoMuestraCrear, db: Session = Depends(get_db)):
    """Crea un nuevo tipo de muestra (E30)."""
    return TipoMuestraService(db).crear(datos)

@router.put("/tipos-muestra/{id}", response_model=TipoMuestraRespuesta)
def actualizar_tipo_muestra(id: int, datos: TipoMuestraActualizar, db: Session = Depends(get_db)):
    """Actualiza un tipo de muestra existente (E31)."""
    return TipoMuestraService(db).actualizar(id, datos)

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO GET /red  (RedVeterinaria)
# TODO POST /red/clinicas  (RedVeterinaria.agregarClinica())
# TODO GET /clinicas
# TODO GET /clinicas/{id}
# TODO PUT /clinicas/{id}
# TODO POST /clinicas/{id}/veterinarios  (Veterinario (alta))
# TODO GET /clinicas/{id}/veterinarios
# TODO PUT /veterinarios/{id}
# TODO DELETE /veterinarios/{id}
# TODO GET /tipos-muestra  (TipoMuestra)
# TODO POST /tipos-muestra  (TipoMuestra (alta))
# TODO PUT /tipos-muestra/{id}
