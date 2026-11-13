"""Unicidad persistente de la red y pertenencia de sus clínicas."""
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.red_veterinaria import RedVeterinaria


def test_base_rechaza_una_segunda_red(db: Session) -> None:
    """La unicidad no depende del nombre, del id ni de pasar por los seeds."""
    db.add(RedVeterinaria(id=7, nombre="Existente"))
    db.commit()

    with Session(db.get_bind()) as otra:
        otra.add(RedVeterinaria(id=23, nombre="Distinta"))
        with pytest.raises(IntegrityError):
            otra.flush()
        otra.rollback()

    assert list(db.execute(select(RedVeterinaria.id, RedVeterinaria.nombre))) == [
        (7, "Existente")
    ]


def test_varias_clinicas_pertenecen_a_la_red(db: Session) -> None:
    """Una única red admite varias clínicas sin cambiar sus relaciones."""
    red = RedVeterinaria(nombre="Red")
    db.add_all([
        ClinicaVeterinaria(nombre="Centro", red=red),
        ClinicaVeterinaria(nombre="Sur", red=red),
    ])
    db.commit()
    db.expire_all()

    assert {clinica.nombre for clinica in red.clinicas} == {"Centro", "Sur"}
    assert all(clinica.red_id == red.id for clinica in red.clinicas)


def test_clinica_no_puede_referenciar_otra_red(db: Session) -> None:
    """La clave foránea evita asociar una clínica a una red inexistente."""
    db.add(ClinicaVeterinaria(nombre="Sin red válida", red_id=999))

    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
