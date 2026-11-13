"""Validación de los schemas del módulo Mascotas."""
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.mascota import MascotaActualizar, MascotaCrear


@pytest.mark.parametrize("nombre", ["", "   ", "\t\n"])
def test_nombre_no_puede_ser_solo_espacios(nombre: str) -> None:
    """Un nombre vacío o hecho solo de espacios no es válido."""
    with pytest.raises(ValidationError):
        MascotaCrear(
            cliente_id=1,
            especie_id=1,
            nombre=nombre,
            fecha_nacimiento=date(2020, 1, 1),
        )


def test_nombre_se_recorta() -> None:
    """Los espacios de los extremos se descartan antes de guardar."""
    mascota = MascotaCrear(
        cliente_id=1,
        especie_id=1,
        nombre="  Luna  ",
        fecha_nacimiento=date(2020, 1, 1),
    )

    assert mascota.nombre == "Luna"


def test_fecha_se_parsea_desde_texto() -> None:
    """Pydantic convierte una fecha ISO en date."""
    mascota = MascotaCrear(
        cliente_id=1,
        especie_id=1,
        nombre="Luna",
        fecha_nacimiento="2020-01-01",
    )

    assert mascota.fecha_nacimiento == date(2020, 1, 1)


def test_actualizar_valida_igual_que_crear() -> None:
    """El schema de reemplazo comparte las validaciones del alta."""
    with pytest.raises(ValidationError):
        MascotaActualizar(
            cliente_id=1,
            especie_id=1,
            nombre="   ",
            fecha_nacimiento=date(2020, 1, 1),
        )


def test_fecha_nacimiento_futura_no_es_valida() -> None:
    """Una mascota no puede haber nacido mañana."""
    with pytest.raises(ValidationError):
        MascotaCrear(
            cliente_id=1,
            especie_id=1,
            nombre="Luna",
            fecha_nacimiento=date.today() + timedelta(days=1),
        )


def test_actualizar_rechaza_fecha_nacimiento_futura() -> None:
    """El PUT aplica la misma regla que el alta."""
    with pytest.raises(ValidationError):
        MascotaActualizar(
            cliente_id=1,
            especie_id=1,
            nombre="Luna",
            fecha_nacimiento=date.today() + timedelta(days=1),
        )


def test_fecha_nacimiento_de_hoy_es_valida() -> None:
    """Nacer hoy es válido: el límite es estrictamente futuro."""
    mascota = MascotaCrear(
        cliente_id=1,
        especie_id=1,
        nombre="Luna",
        fecha_nacimiento=date.today(),
    )

    assert mascota.fecha_nacimiento == date.today()
