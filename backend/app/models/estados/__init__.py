"""Estados de la muestra (patrón State) y traducción de nombre a clase."""
from app.models.estados.analizada import Analizada
from app.models.estados.empaquetada import Empaquetada
from app.models.estados.en_transito import EnTransito
from app.models.estados.estado import Estado
from app.models.estados.extraida import Extraida
from app.models.estados.recibida import Recibida
from app.models.estados.rechazada import Rechazada

ESTADOS: dict[str, type[Estado]] = {
    "Extraida": Extraida,
    "Empaquetada": Empaquetada,
    "EnTransito": EnTransito,
    "Recibida": Recibida,
    "Analizada": Analizada,
    "Rechazada": Rechazada,
}


def estado_desde_nombre(nombre: str) -> Estado:
    """Devuelve una instancia del estado que corresponde al nombre guardado en la base."""
    return ESTADOS[nombre]()
