"""Estado Analizada de una muestra biológica."""
from app.models.estados.estado import Estado


class Analizada(Estado):
    nombre = "Analizada"

    def puede_pasar_a(self, otro: Estado) -> bool:
        """Analizada es un estado final: no tiene transiciones salientes."""
        return False
