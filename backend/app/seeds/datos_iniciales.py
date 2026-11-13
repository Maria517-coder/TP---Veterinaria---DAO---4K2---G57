"""Carga los datos que deben existir antes de usar el sistema."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.especie import Especie
from app.models.estado_catalogo import EstadoCatalogo
from app.models.tipo_muestra import TipoMuestra

ESTADOS = (
    "Extraida",
    "Empaquetada",
    "EnTransito",
    "Recibida",
    "Analizada",
    "Rechazada",
)

ESPECIES = ("PERRO", "GATO", "OTRO")

TIPOS_MUESTRA: dict[str, Decimal] = {
    "SANGRE": Decimal("1500.00"),
    "ORINA": Decimal("1200.00"),
    "HECES": Decimal("1000.00"),
    "HISOPADO": Decimal("1800.00"),
    "TEJIDO": Decimal("2500.00"),
}


def _existe(db: Session, modelo: type, nombre: str) -> bool:
    """Indica si ya hay una fila con ese nombre en el catálogo."""
    return db.scalar(select(modelo.id).where(modelo.nombre == nombre)) is not None


def cargar_datos_iniciales(db: Session) -> None:
    """Carga los 6 estados de muestra, las especies y los tipos de muestra.

    Es idempotente: solo inserta los nombres que faltan, así que se puede
    ejecutar en cada arranque sin duplicar filas. El llamador confirma o revierte
    la transacción; esta función solo envía las inserciones a la base.
    """
    for nombre in ESTADOS:
        if not _existe(db, EstadoCatalogo, nombre):
            db.add(EstadoCatalogo(nombre=nombre))

    for nombre in ESPECIES:
        if not _existe(db, Especie, nombre):
            db.add(Especie(nombre=nombre))

    for nombre, costo in TIPOS_MUESTRA.items():
        if not _existe(db, TipoMuestra, nombre):
            db.add(TipoMuestra(nombre=nombre, costo_analisis=costo))

    db.flush()
