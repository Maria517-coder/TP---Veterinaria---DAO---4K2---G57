"""Estado Analizada de una muestra biológica."""
from app.models.estados.estado import Estado


class Analizada(Estado):
    nombre = "Analizada"

    def puede_pasar_a(self, otro: Estado) -> bool:
        raise NotImplementedError("TODO: desde Analizada se puede pasar a: ninguno (estado final)")
