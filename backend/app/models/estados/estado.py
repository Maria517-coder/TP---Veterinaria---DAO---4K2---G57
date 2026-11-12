"""Patrón State: clase abstracta de los estados de una muestra biológica."""
from abc import ABC, abstractmethod


class Estado(ABC):
    nombre: str

    @abstractmethod
    def puede_pasar_a(self, otro: "Estado") -> bool:
        """Indica si la muestra puede pasar desde este estado al estado `otro`."""
