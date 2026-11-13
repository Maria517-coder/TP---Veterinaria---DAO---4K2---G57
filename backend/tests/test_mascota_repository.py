"""Tests directos del MascotaRepository, sin pasar por HTTP."""
from datetime import date

from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.repositories.mascota_repository import MascotaRepository


def _crear_cliente(db: Session, nombre: str = "Ana") -> Cliente:
    """Inserta un cliente ya confirmado para usarlo como dato de prueba."""
    cliente = Cliente(nombre=nombre, telefono="123")
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def _crear_especie(db: Session, nombre: str = "PERRO") -> Especie:
    """Inserta una especie ya confirmada para usarla como dato de prueba."""
    especie = Especie(nombre=nombre)
    db.add(especie)
    db.commit()
    db.refresh(especie)
    return especie


def _crear_mascota(
    db: Session,
    cliente: Cliente,
    especie: Especie,
    nombre: str = "Luna",
    activo: bool = True,
) -> Mascota:
    """Inserta una mascota ya confirmada para usarla como dato de prueba."""
    mascota = Mascota(
        cliente_id=cliente.id,
        especie_id=especie.id,
        nombre=nombre,
        fecha_nacimiento=date(2020, 1, 1),
        activo=activo,
    )
    db.add(mascota)
    db.commit()
    db.refresh(mascota)
    return mascota


def test_guardar_asigna_id_y_no_hace_commit(db: Session) -> None:
    """guardar hace flush (asigna id) pero deja la transacción abierta."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    repositorio = MascotaRepository(db)

    mascota = repositorio.guardar(
        Mascota(
            cliente_id=cliente.id,
            especie_id=especie.id,
            nombre="Luna",
            fecha_nacimiento=date(2020, 1, 1),
        )
    )
    mascota_id = mascota.id

    assert mascota_id is not None
    db.rollback()
    assert db.get(Mascota, mascota_id) is None


def test_guardar_historia_asigna_id_y_no_hace_commit(db: Session) -> None:
    """guardar_historia hace flush pero deja la transacción abierta."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    mascota = _crear_mascota(db, cliente, especie)
    repositorio = MascotaRepository(db)

    historia = repositorio.guardar_historia(
        HistoriaClinica(mascota_id=mascota.id, numero=mascota.id)
    )
    historia_id = historia.id

    assert historia_id is not None
    db.rollback()
    assert db.get(HistoriaClinica, historia_id) is None


def test_buscar_por_id_devuelve_la_activa(db: Session) -> None:
    """buscar_por_id encuentra una mascota activa."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    mascota = _crear_mascota(db, cliente, especie)

    encontrada = MascotaRepository(db).buscar_por_id(mascota.id)

    assert encontrada is not None
    assert encontrada.nombre == "Luna"


def test_buscar_por_id_ignora_la_inactiva(db: Session) -> None:
    """Una mascota dada de baja se comporta como inexistente."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    mascota = _crear_mascota(db, cliente, especie, activo=False)

    assert MascotaRepository(db).buscar_por_id(mascota.id) is None


def test_buscar_por_id_inexistente_devuelve_none(db: Session) -> None:
    """Un id que no existe devuelve None."""
    assert MascotaRepository(db).buscar_por_id(9999) is None


def test_listar_devuelve_solo_activas(db: Session) -> None:
    """listar filtra por activo aunque no se pase ningún filtro."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    _crear_mascota(db, cliente, especie, "Luna")
    _crear_mascota(db, cliente, especie, "Michi", activo=False)

    nombres = [mascota.nombre for mascota in MascotaRepository(db).listar()]

    assert nombres == ["Luna"]


def test_listar_filtra_por_cliente(db: Session) -> None:
    """El filtro por cliente_id solo devuelve mascotas de ese responsable."""
    ana = _crear_cliente(db, "Ana")
    bruno = _crear_cliente(db, "Bruno")
    especie = _crear_especie(db)
    _crear_mascota(db, ana, especie, "Luna")
    _crear_mascota(db, bruno, especie, "Firulais")

    nombres = [
        mascota.nombre
        for mascota in MascotaRepository(db).listar(cliente_id=ana.id)
    ]

    assert nombres == ["Luna"]


def test_listar_filtra_por_especie(db: Session) -> None:
    """El filtro por especie_id solo devuelve mascotas de esa especie."""
    cliente = _crear_cliente(db)
    perro = _crear_especie(db, "PERRO")
    gato = _crear_especie(db, "GATO")
    _crear_mascota(db, cliente, perro, "Luna")
    _crear_mascota(db, cliente, gato, "Michi")

    nombres = [
        mascota.nombre
        for mascota in MascotaRepository(db).listar(especie_id=gato.id)
    ]

    assert nombres == ["Michi"]


def test_listar_combina_filtros(db: Session) -> None:
    """Los filtros de cliente y especie se aplican juntos."""
    ana = _crear_cliente(db, "Ana")
    bruno = _crear_cliente(db, "Bruno")
    perro = _crear_especie(db, "PERRO")
    gato = _crear_especie(db, "GATO")
    _crear_mascota(db, ana, perro, "Luna")
    _crear_mascota(db, ana, gato, "Michi")
    _crear_mascota(db, bruno, perro, "Firulais")

    nombres = [
        mascota.nombre
        for mascota in MascotaRepository(db).listar(
            cliente_id=ana.id, especie_id=perro.id
        )
    ]

    assert nombres == ["Luna"]


def test_buscar_especie_devuelve_la_existente(db: Session) -> None:
    """buscar_especie encuentra la especie por id."""
    especie = _crear_especie(db, "GATO")

    encontrada = MascotaRepository(db).buscar_especie(especie.id)

    assert encontrada is not None
    assert encontrada.nombre == "GATO"


def test_buscar_especie_inexistente_devuelve_none(db: Session) -> None:
    """Una especie inexistente devuelve None."""
    assert MascotaRepository(db).buscar_especie(9999) is None
