"""Estado Empaquetada de una muestra biológica."""
from app.models.estados.estado import Estado


class Empaquetada(Estado):
    nombre = "Empaquetada"

    def puede_pasar_a(self, otro: Estado) -> bool:
        raise NotImplementedError("TODO: desde Empaquetada se puede pasar a: solo a EnTransito")
