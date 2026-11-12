"""Estados del ciclo de vida del remito biológico."""
import enum


class EstadoRemito(str, enum.Enum):
    GENERADO = "GENERADO"
    DESPACHADO = "DESPACHADO"
    RECIBIDO = "RECIBIDO"
    CERRADO = "CERRADO"
