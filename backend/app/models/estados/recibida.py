"""Estado Recibida de una muestra biológica."""
from app.models.estados.analizada import Analizada
from app.models.estados.estado import Estado


class Recibida(Estado):
    nombre = "Recibida"

    def puede_pasar_a(self, otro: Estado) -> bool:
        """Desde Recibida solo se puede pasar a Analizada."""
        return isinstance(otro, Analizada)
