"""Validación de los schemas de red y clínicas."""
import pytest
from pydantic import ValidationError

from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.red_veterinaria import RedVeterinaria
from app.schemas.clinica import (
    ClinicaVeterinariaActualizar,
    ClinicaVeterinariaCrear,
    ClinicaVeterinariaRespuesta,
)
from app.schemas.red import RedVeterinariaRespuesta


@pytest.mark.parametrize("nombre", ["", "   ", "\t\n", "N" * 101])
def test_nombre_clinica_invalido(nombre: str) -> None:
    """El nombre no puede ser vacío ni superar los 100 caracteres."""
    with pytest.raises(ValidationError):
        ClinicaVeterinariaCrear(nombre=nombre)


def test_nombre_clinica_se_recorta() -> None:
    """Los espacios de los extremos se descartan."""
    assert ClinicaVeterinariaCrear(nombre="  Centro  ").nombre == "Centro"


def test_actualizar_valida_igual_que_crear() -> None:
    """El PUT comparte las validaciones del alta."""
    with pytest.raises(ValidationError):
        ClinicaVeterinariaActualizar(nombre="")
    assert ClinicaVeterinariaActualizar(nombre="  Sur ").nombre == "Sur"


def test_respuesta_red_solo_id_y_nombre() -> None:
    """E20 devuelve la red sin las clínicas anidadas."""
    red = RedVeterinaria(id=1, nombre="Red")

    assert RedVeterinariaRespuesta.model_validate(red).model_dump() == {
        "id": 1,
        "nombre": "Red",
    }


def test_respuesta_clinica_desde_modelo() -> None:
    """La respuesta se arma desde los atributos del modelo."""
    clinica = ClinicaVeterinaria(id=2, red_id=1, nombre="Centro", activo=True)

    assert ClinicaVeterinariaRespuesta.model_validate(clinica).model_dump() == {
        "id": 2,
        "nombre": "Centro",
        "red_id": 1,
        "activo": True,
    }
