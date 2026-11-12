"""Carga los datos que deben existir antes de usar el sistema."""
from sqlalchemy.orm import Session


def cargar_datos_iniciales(db: Session) -> None:
    """Carga los 6 estados de muestra, las especies y los tipos de muestra.

    Debe poder ejecutarse varias veces sin duplicar filas.
    """
    # TODO: estados: Extraida, Empaquetada, EnTransito, Recibida, Analizada, Rechazada
    # TODO: especies: PERRO, GATO, OTRO
    # TODO: tipos de muestra con su costo de análisis
    raise NotImplementedError("TODO: cargar datos iniciales")
