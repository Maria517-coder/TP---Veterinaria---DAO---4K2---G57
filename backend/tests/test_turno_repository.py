"""Consultas y guardado de turnos en el repository."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.models.red_veterinaria import RedVeterinaria
from app.models.turno import Turno
from app.models.veterinario import Veterinario
from app.repositories.turno_repository import TurnoRepository


@pytest.fixture()
def turnos(db: Session) -> tuple[int, datetime]:
    """Dos turnos activos y uno cancelado, con fechas relativas."""
    red = RedVeterinaria(nombre="Red")
    db.add(red)
    db.flush()
    clinica = ClinicaVeterinaria(nombre="Centro", red=red)
    db.add(clinica)
    db.flush()
    veterinario = Veterinario(
        nombre="Eva", matricula="MP-1", clinica=clinica
    )
    especie = Especie(nombre="PERRO")
    cliente = Cliente(nombre="Ana", telefono="123")
    db.add_all([veterinario, especie, cliente])
    db.flush()
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=datetime.now().date() - timedelta(days=365),
        responsable=cliente,
        especie=especie,
        historia_clinica=HistoriaClinica(numero=1),
    )
    db.add(mascota)
    db.flush()
    base = datetime.now() + timedelta(days=1)
    db.add_all(
        [
            Turno(
                veterinario=veterinario,
                mascota=mascota,
                inicio=base,
                fin=base + timedelta(minutes=30),
                activo=True,
            ),
            Turno(
                veterinario=veterinario,
                mascota=mascota,
                inicio=base + timedelta(hours=2),
                fin=base + timedelta(hours=2, minutes=30),
                activo=True,
            ),
            Turno(
                veterinario=veterinario,
                mascota=mascota,
                inicio=base + timedelta(hours=4),
                fin=base + timedelta(hours=4, minutes=30),
                activo=False,
            ),
        ]
    )
    db.commit()
    return veterinario.id, base


def test_buscar_por_id(db: Session, turnos: tuple[int, datetime]) -> None:
    repositorio = TurnoRepository(db)
    todos = repositorio.listar_por_veterinario(turnos[0])

    assert repositorio.buscar_por_id(todos[0].id).id == todos[0].id
    assert repositorio.buscar_por_id(9999) is None


def test_listar_por_veterinario_solo_activos(
    db: Session, turnos: tuple[int, datetime]
) -> None:
    activos = TurnoRepository(db).listar_por_veterinario(turnos[0])

    assert len(activos) == 2
    assert all(turno.activo for turno in activos)
    assert [turno.inicio for turno in activos] == sorted(
        turno.inicio for turno in activos
    )


def test_listar_con_filtro_por_fecha(
    db: Session, turnos: tuple[int, datetime]
) -> None:
    repositorio = TurnoRepository(db)
    todos = repositorio.listar_por_veterinario(turnos[0])
    fecha = turnos[1].date()

    assert repositorio.listar_por_veterinario(turnos[0], fecha) == todos
    assert (
        repositorio.listar_por_veterinario(
            turnos[0], fecha + timedelta(days=2)
        )
        == []
    )


def test_guardar_hace_flush_sin_commit(
    db: Session, turnos: tuple[int, datetime]
) -> None:
    repositorio = TurnoRepository(db)
    veterinario_id, base = turnos
    veterinario = db.get(Veterinario, veterinario_id)
    assert veterinario is not None
    turno = Turno(
        veterinario=veterinario,
        mascota=veterinario.turnos[0].mascota,
        inicio=base + timedelta(hours=6),
        fin=base + timedelta(hours=6, minutes=30),
        activo=True,
    )

    guardado = repositorio.guardar(turno)

    assert guardado.id is not None
    db.rollback()
    assert db.get(Turno, guardado.id) is None
