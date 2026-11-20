"""Estado Rechazada de una muestra biológica."""
from app.models.estados.estado import Estado


class Rechazada(Estado):
    nombre = "Rechazada"

    def puede_pasar_a(self, otro: Estado) -> bool:
        """Rechazada es un estado final: no tiene transiciones salientes."""
        return False
