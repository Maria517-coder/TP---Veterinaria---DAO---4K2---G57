"""Estado Extraida de una muestra biológica."""
from app.models.estados.empaquetada import Empaquetada
from app.models.estados.estado import Estado


class Extraida(Estado):
    nombre = "Extraida"

    def puede_pasar_a(self, otro: Estado) -> bool:
        """Desde Extraida solo se puede pasar a Empaquetada."""
        return isinstance(otro, Empaquetada)
