"""Validación de los schemas del módulo Clientes."""
import pytest
from pydantic import ValidationError

from app.schemas.cliente import ClienteCrear


@pytest.mark.parametrize("nombre", ["", "   ", "\t\n"])
def test_nombre_no_puede_ser_solo_espacios(nombre: str) -> None:
    """Un nombre vacío o hecho solo de espacios no es un nombre válido."""
    with pytest.raises(ValidationError):
        ClienteCrear(nombre=nombre, telefono="123")


def test_nombre_y_telefono_se_recortan() -> None:
    """Los espacios de los extremos se descartan antes de guardar."""
    cliente = ClienteCrear(nombre="  Ana  ", telefono=" 123 ")

    assert cliente.nombre == "Ana"
    assert cliente.telefono == "123"
