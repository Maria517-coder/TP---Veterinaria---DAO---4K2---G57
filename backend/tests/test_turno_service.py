"""Casos de uso de agenda y turnos: validaciones, transacción y baja lógica."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontrado, TurnoSuperpuesto
from app.models.cliente import Cliente
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.models.red_veterinaria import RedVeterinaria
from app.models.turno import Turno
from app.models.veterinario import Veterinario
from app.repositories.turno_repository import TurnoRepository
from app.schemas.turno import TurnoCrear, TurnoDisponibilidad
from app.services.turno_service import TurnoService


@pytest.fixture()
def ctx(db: Session) -> dict:
    """Arma el grafo mínimo, con un veterinario y una mascota dados de baja."""
    red = RedVeterinaria(nombre="Red S")
    db.add(red)
    db.flush()
    clinica = ClinicaVeterinaria(nombre="Centro", red=red)
    db.add(clinica)
    db.flush()
    veterinario = Veterinario(nombre="Eva", matricula="MP-1", clinica=clinica)
    veterinario_baja = Veterinario(
        nombre="Baja", matricula="MP-2", clinica=clinica, activo=False
    )
    especie = Especie(nombre="PERRO")
    cliente = Cliente(nombre="Ana", telefono="123")
    db.add_all([veterinario, veterinario_baja, especie, cliente])
    db.flush()
    nacimiento = datetime.now().date() - timedelta(days=365)
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=nacimiento,
        responsable=cliente,
        especie=especie,
        historia_clinica=HistoriaClinica(numero=1),
    )
    mascota_baja = Mascota(
        nombre="Sol",
        fecha_nacimiento=nacimiento,
        responsable=cliente,
        especie=especie,
        activo=False,
        historia_clinica=HistoriaClinica(numero=2),
    )
    db.add_all([mascota, mascota_baja])
    db.commit()
    return {
        "vet": veterinario.id,
        "vet_baja": veterinario_baja.id,
        "mascota": mascota.id,
        "mascota_baja": mascota_baja.id,
        "base": datetime.now() + timedelta(days=1),
    }


def _crear(
    db: Session, ctx: dict, desde: int = 0, hasta: int = 30, mascota_id: int | None = None
) -> Turno:
    base = ctx["base"]
    return TurnoService(db).crear(
        ctx["vet"],
        TurnoCrear(
            mascota_id=mascota_id if mascota_id is not None else ctx["mascota"],
            inicio=base + timedelta(minutes=desde),
            fin=base + timedelta(minutes=hasta),
        ),
    )


def test_crear_turno_valido(db: Session, ctx: dict) -> None:
    turno = _crear(db, ctx)

    assert turno.id is not None
    assert turno.activo is True
    assert TurnoRepository(db).buscar_por_id(turno.id).id == turno.id


def test_crear_rechaza_veterinario_inexistente_o_inactivo(
    db: Session, ctx: dict
) -> None:
    servicio = TurnoService(db)
    datos = TurnoCrear(
        mascota_id=ctx["mascota"],
        inicio=ctx["base"],
        fin=ctx["base"] + timedelta(minutes=30),
    )

    with pytest.raises(RecursoNoEncontrado, match="veterinario"):
        servicio.crear(9999, datos)
    with pytest.raises(RecursoNoEncontrado, match="veterinario"):
        servicio.crear(ctx["vet_baja"], datos)


def test_crear_rechaza_mascota_inexistente_o_inactiva(db: Session, ctx: dict) -> None:
    """Criterio decisión 5: inactiva = inexistente, luego 404 (no 409)."""
    with pytest.raises(RecursoNoEncontrado, match="mascota"):
        _crear(db, ctx, mascota_id=9999)
    with pytest.raises(RecursoNoEncontrado, match="mascota"):
        _crear(db, ctx, mascota_id=ctx["mascota_baja"])


def test_crear_rechaza_superposicion_y_no_guarda(db: Session, ctx: dict) -> None:
    _crear(db, ctx, 0, 60)

    with pytest.raises(TurnoSuperpuesto):
        _crear(db, ctx, 30, 90)

    assert len(TurnoRepository(db).listar_por_veterinario(ctx["vet"])) == 1


def test_turno_cancelado_no_bloquea_nuevo_turno(db: Session, ctx: dict) -> None:
    """Decisión 9: el horario liberado se puede volver a reservar."""
    servicio = TurnoService(db)
    primero = _crear(db, ctx, 0, 60)
    servicio.cancelar(primero.id)

    nuevo = _crear(db, ctx, 0, 60)

    assert nuevo.id != primero.id
    assert [turno.id for turno in servicio.listar_agenda(ctx["vet"])] == [nuevo.id]


def test_orden_validacion_mascota_antes_que_superposicion(
    db: Session, ctx: dict
) -> None:
    """Si fallan dos reglas, gana la de existencia (404 antes que 409)."""
    _crear(db, ctx, 0, 60)

    with pytest.raises(RecursoNoEncontrado, match="mascota"):
        _crear(db, ctx, 30, 90, mascota_id=9999)


def test_listar_agenda_filtra_cancelados_y_ordena(db: Session, ctx: dict) -> None:
    servicio = TurnoService(db)
    cancelado = _crear(db, ctx, 0, 30)
    servicio.cancelar(cancelado.id)
    segundo = _crear(db, ctx, 60, 90)
    primero = _crear(db, ctx, 120, 150)

    assert [turno.id for turno in servicio.listar_agenda(ctx["vet"])] == [
        segundo.id,
        primero.id,
    ]
    assert [
        turno.id for turno in servicio.listar_agenda(ctx["vet"], ctx["base"].date())
    ] == [segundo.id, primero.id]
    assert (
        servicio.listar_agenda(ctx["vet"], (ctx["base"] + timedelta(days=2)).date())
        == []
    )


def test_disponibilidad(db: Session, ctx: dict) -> None:
    servicio = TurnoService(db)
    base = ctx["base"]
    libre = TurnoDisponibilidad(inicio=base, fin=base + timedelta(minutes=30))
    superpuesto = TurnoDisponibilidad(
        inicio=base + timedelta(minutes=30), fin=base + timedelta(minutes=90)
    )
    limite = TurnoDisponibilidad(
        inicio=base + timedelta(minutes=60), fin=base + timedelta(minutes=90)
    )

    assert servicio.consultar_disponibilidad(ctx["vet"], libre) is True
    _crear(db, ctx, 0, 60)
    assert servicio.consultar_disponibilidad(ctx["vet"], superpuesto) is False
    assert servicio.consultar_disponibilidad(ctx["vet"], limite) is True


def test_consultas_rechazan_veterinario_inactivo(db: Session, ctx: dict) -> None:
    servicio = TurnoService(db)
    base = ctx["base"]
    intervalo = TurnoDisponibilidad(inicio=base, fin=base + timedelta(minutes=30))

    with pytest.raises(RecursoNoEncontrado, match="veterinario"):
        servicio.listar_agenda(ctx["vet_baja"])
    with pytest.raises(RecursoNoEncontrado, match="veterinario"):
        servicio.consultar_disponibilidad(ctx["vet_baja"], intervalo)


def test_cancelar_es_baja_logica(db: Session, ctx: dict) -> None:
    servicio = TurnoService(db)
    turno = _crear(db, ctx)

    servicio.cancelar(turno.id)

    guardado = db.get(Turno, turno.id)
    assert guardado is not None
    assert guardado.activo is False
    assert TurnoRepository(db).buscar_por_id(turno.id) is None


def test_cancelar_inexistente_da_404(db: Session, ctx: dict) -> None:
    with pytest.raises(RecursoNoEncontrado, match="turno"):
        TurnoService(db).cancelar(9999)
