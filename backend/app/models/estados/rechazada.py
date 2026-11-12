"""Estado Rechazada de una muestra biológica."""
from app.models.estados.estado import Estado


class Rechazada(Estado):
    nombre = "Rechazada"

    def puede_pasar_a(self, otro: Estado) -> bool:
        raise NotImplementedError("TODO: desde Rechazada se puede pasar a: ninguno (estado final)")
