"""Integridad de la base: claves foráneas activas, NOT NULL y UNIQUE."""
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota


def _crear_especie(db: Session) -> Especie:
    """Inserta una especie para poder crear mascotas."""
    especie = Especie(nombre="PERRO")
    db.add(especie)
    db.flush()
    return especie


def _crear_cliente(db: Session) -> Cliente:
    """Inserta un cliente responsable."""
    cliente = Cliente(nombre="Ana", telefono="123")
    db.add(cliente)
    db.flush()
    return cliente


def test_fk_inexistente_falla(db: Session) -> None:
    """Una mascota no puede apuntar a un cliente que no existe."""
    especie = _crear_especie(db)
    db.add(
        Mascota(
            cliente_id=9999,
            especie_id=especie.id,
            nombre="Firulais",
            fecha_nacimiento=date(2020, 1, 1),
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_mascota_sin_cliente_falla(db: Session) -> None:
    """Toda mascota tiene un responsable obligatorio: cliente_id no puede ser NULL."""
    especie = _crear_especie(db)
    db.add(
        Mascota(
            especie_id=especie.id,
            nombre="Michi",
            fecha_nacimiento=date(2021, 6, 15),
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()


def test_mascota_con_dos_historias_falla(db: Session) -> None:
    """Cada mascota tiene exactamente una historia clínica."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    mascota = Mascota(
        cliente_id=cliente.id,
        especie_id=especie.id,
        nombre="Luna",
        fecha_nacimiento=date(2019, 3, 10),
    )
    db.add(mascota)
    db.flush()

    db.add(HistoriaClinica(mascota_id=mascota.id, numero=1))
    db.flush()

    db.add(HistoriaClinica(mascota_id=mascota.id, numero=2))
    with pytest.raises(IntegrityError):
        db.flush()
