"""Carga los datos que deben existir antes de usar el sistema."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateIndex

from app.exceptions import ReglaDeNegocioViolada
from app.models.especie import Especie
from app.models.estado_catalogo import EstadoCatalogo
from app.models.red_veterinaria import INDICE_RED_UNICA, RedVeterinaria
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


def _inicializar_red(db: Session) -> None:
    """Reutiliza la red o prepara su creación sin alterar datos inconsistentes."""
    with db.no_autoflush:
        redes = list(db.scalars(select(RedVeterinaria).limit(2)))
    redes.extend(objeto for objeto in db.new if isinstance(objeto, RedVeterinaria))
    if len(redes) > 1:
        raise ReglaDeNegocioViolada(
            "No se puede inicializar el sistema: existen varias redes veterinarias. "
            "Los datos existentes no se modificaron."
        )
    if not redes:
        db.add(RedVeterinaria(nombre="Red Veterinaria"))


def cargar_datos_iniciales(db: Session) -> None:
    """Inicializa la red única y los catálogos de estados, especies y muestras.

    Es idempotente: solo inserta los nombres que faltan, así que se puede
    ejecutar en cada arranque sin duplicar filas. El llamador confirma o revierte
    la transacción; esta función solo envía las inserciones a la base.
    """
    _inicializar_red(db)

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
    # SQLite verifica la existencia: la reflexión omite índices sobre expresiones.
    db.execute(CreateIndex(INDICE_RED_UNICA, if_not_exists=True))
