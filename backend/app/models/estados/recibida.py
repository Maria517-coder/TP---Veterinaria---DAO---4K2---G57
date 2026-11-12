"""Estado Recibida de una muestra biológica."""
from app.models.estados.estado import Estado


class Recibida(Estado):
    nombre = "Recibida"

    def puede_pasar_a(self, otro: Estado) -> bool:
        raise NotImplementedError("TODO: desde Recibida se puede pasar a: solo a Analizada")
