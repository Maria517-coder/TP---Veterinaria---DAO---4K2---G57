"""Estado Extraida de una muestra biológica."""
from app.models.estados.estado import Estado


class Extraida(Estado):
    nombre = "Extraida"

    def puede_pasar_a(self, otro: Estado) -> bool:
        raise NotImplementedError("TODO: desde Extraida se puede pasar a: solo a Empaquetada")
