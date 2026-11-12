"""Estado EnTransito de una muestra biológica."""
from app.models.estados.estado import Estado


class EnTransito(Estado):
    nombre = "EnTransito"

    def puede_pasar_a(self, otro: Estado) -> bool:
        raise NotImplementedError("TODO: desde EnTransito se puede pasar a: a Recibida o a Rechazada")
