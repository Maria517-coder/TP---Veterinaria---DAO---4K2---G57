"""Seeds: carga de catálogos iniciales e idempotencia."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.especie import Especie
from app.models.estado_catalogo import EstadoCatalogo
from app.models.tipo_muestra import TipoMuestra
from app.seeds.datos_iniciales import cargar_datos_iniciales

ESTADOS_ESPERADOS = {
    "Extraida",
    "Empaquetada",
    "EnTransito",
    "Recibida",
    "Analizada",
    "Rechazada",
}

ESPECIES_ESPERADAS = {"PERRO", "GATO", "OTRO"}

TIPOS_ESPERADOS = {
    "SANGRE": 1500.0,
    "ORINA": 1200.0,
    "HECES": 1000.0,
    "HISOPADO": 1800.0,
    "TEJIDO": 2500.0,
}


def _contar(db: Session, modelo: type) -> int:
    """Cuenta las filas de una tabla."""
    return db.scalar(select(func.count()).select_from(modelo)) or 0


def test_seed_carga_los_catalogos(db: Session) -> None:
    """El seed deja los estados, las especies y los tipos de muestra esperados."""
    cargar_datos_iniciales(db)

    estados = set(db.scalars(select(EstadoCatalogo.nombre)))
    especies = set(db.scalars(select(Especie.nombre)))
    tipos = {
        tipo.nombre: tipo.costo_analisis
        for tipo in db.scalars(select(TipoMuestra))
    }

    assert estados == ESTADOS_ESPERADOS
    assert especies == ESPECIES_ESPERADAS
    assert tipos == TIPOS_ESPERADOS


def test_seed_es_idempotente(db: Session) -> None:
    """Correr el seed dos veces no duplica filas."""
    cargar_datos_iniciales(db)
    cargar_datos_iniciales(db)

    assert _contar(db, EstadoCatalogo) == len(ESTADOS_ESPERADOS)
    assert _contar(db, Especie) == len(ESPECIES_ESPERADAS)
    assert _contar(db, TipoMuestra) == len(TIPOS_ESPERADOS)
