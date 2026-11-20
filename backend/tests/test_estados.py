"""Reglas del patrón State: a qué estado puede pasar una muestra desde cada estado."""
import pytest

from app.models.estados import (
    Analizada,
    Empaquetada,
    EnTransito,
    Extraida,
    Rechazada,
    Recibida,
)

TODOS = [Extraida, Empaquetada, EnTransito, Recibida, Analizada, Rechazada]

TRANSICIONES_VALIDAS = {
    Extraida: {Empaquetada},
    Empaquetada: {EnTransito},
    EnTransito: {Recibida, Rechazada},
    Recibida: {Analizada},
    Analizada: set(),
    Rechazada: set(),
}


@pytest.mark.parametrize("origen", TODOS)
@pytest.mark.parametrize("destino", TODOS)
def test_matriz_de_transiciones(origen, destino):
    esperado = destino in TRANSICIONES_VALIDAS[origen]
    assert origen().puede_pasar_a(destino()) is esperado