"""La red asigna sus clínicas: RedVeterinaria.agregar_clinica()."""
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ReglaDeNegocioViolada
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.red_veterinaria import RedVeterinaria


def test_agregar_clinica_asigna_la_red(db: Session) -> None:
    """El método vincula la clínica con la red en los dos sentidos."""
    red = RedVeterinaria(nombre="Red")
    db.add(red)
    db.flush()
    clinica = ClinicaVeterinaria(nombre="Centro")
    db.add(clinica)

    red.agregar_clinica(clinica)
    db.flush()

    assert clinica.red is red
    assert clinica.red_id == red.id
    assert clinica in red.clinicas


def test_agregar_clinica_rechaza_none(db: Session) -> None:
    """No se puede agregar una referencia nula: error claro antes de mutar."""
    red = RedVeterinaria(nombre="Red")

    with pytest.raises(ReglaDeNegocioViolada, match="clínica"):
        red.agregar_clinica(None)  # type: ignore[arg-type]


def test_agregar_clinica_no_confirma(db: Session) -> None:
    """El modelo no hace commit: si el llamador revierte, no queda clínica."""
    red = RedVeterinaria(nombre="Red")
    db.add(red)
    db.flush()

    clinica = ClinicaVeterinaria(nombre="Centro")
    db.add(clinica)
    red.agregar_clinica(clinica)
    db.flush()
    db.rollback()

    assert (
        db.scalar(
            select(ClinicaVeterinaria).where(ClinicaVeterinaria.nombre == "Centro")
        )
        is None
    )
