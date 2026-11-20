"""Estado EnTransito de una muestra biológica."""
from app.models.estados.estado import Estado
from app.models.estados.rechazada import Rechazada
from app.models.estados.recibida import Recibida


class EnTransito(Estado):
    nombre = "EnTransito"

    def puede_pasar_a(self, otro: Estado) -> bool:
        """Desde EnTransito se puede pasar a Recibida o a Rechazada."""
        return isinstance(otro, (Recibida, Rechazada))
