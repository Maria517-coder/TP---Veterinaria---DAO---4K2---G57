"""Estado Empaquetada de una muestra biológica."""
from app.models.estados.en_transito import EnTransito
from app.models.estados.estado import Estado


class Empaquetada(Estado):
    nombre = "Empaquetada"

    def puede_pasar_a(self, otro: Estado) -> bool:
        """Desde Empaquetada solo se puede pasar a EnTransito."""
        return isinstance(otro, EnTransito)
