"""Excepciones propias del dominio; un manejador global las traduce a respuestas HTTP."""


class ErrorDeDominio(Exception):
    """Base de todos los errores del dominio."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class RecursoNoEncontrado(ErrorDeDominio):
    """El recurso pedido no existe (HTTP 404)."""


class TransicionInvalida(ErrorDeDominio):
    """Cambio de estado no permitido por el patrón State (HTTP 409)."""


class TurnoSuperpuesto(ErrorDeDominio):
    """El turno se superpone con otro de la agenda del veterinario (HTTP 409)."""


class ReglaDeNegocioViolada(ErrorDeDominio):
    """Se incumple una regla de negocio de la consigna (HTTP 422)."""


class ConflictoDeRecurso(ErrorDeDominio):
    """La operación choca con el estado actual del recurso (HTTP 409)."""
