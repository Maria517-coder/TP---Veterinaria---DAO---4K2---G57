"""Tests directos del ClienteRepository, sin pasar por HTTP."""
from datetime import date

from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.especie import Especie
from app.models.mascota import Mascota
from app.repositories.cliente_repository import ClienteRepository


def _crear_cliente(db: Session, nombre: str = "Ana", activo: bool = True) -> Cliente:
    """Inserta un cliente ya confirmado para usarlo como dato de prueba."""
    cliente = Cliente(nombre=nombre, telefono="123", activo=activo)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def test_guardar_asigna_id_y_no_hace_commit(db: Session) -> None:
    """guardar hace flush (asigna id) pero deja la transacción abierta."""
    repositorio = ClienteRepository(db)

    cliente = repositorio.guardar(Cliente(nombre="Ana", telefono="123"))
    cliente_id = cliente.id

    assert cliente_id is not None
    db.rollback()
    assert db.get(Cliente, cliente_id) is None


def test_buscar_por_id_devuelve_el_activo(db: Session) -> None:
    """buscar_por_id encuentra un cliente activo."""
    cliente = _crear_cliente(db)

    encontrado = ClienteRepository(db).buscar_por_id(cliente.id)

    assert encontrado is not None
    assert encontrado.nombre == "Ana"


def test_buscar_por_id_ignora_el_inactivo(db: Session) -> None:
    """Un cliente dado de baja se comporta como inexistente."""
    cliente = _crear_cliente(db, activo=False)

    assert ClienteRepository(db).buscar_por_id(cliente.id) is None


def test_buscar_por_id_inexistente_devuelve_none(db: Session) -> None:
    """Un id que no existe devuelve None."""
    assert ClienteRepository(db).buscar_por_id(9999) is None


def test_listar_devuelve_solo_activos(db: Session) -> None:
    """listar filtra por activo aunque no se pase nombre."""
    _crear_cliente(db, "Ana")
    _crear_cliente(db, "Bruno", activo=False)

    nombres = [cliente.nombre for cliente in ClienteRepository(db).listar()]

    assert nombres == ["Ana"]


def test_listar_filtra_por_nombre_parcial_sin_distinguir_mayusculas(db: Session) -> None:
    """El filtro es un `contains` que no distingue mayúsculas y solo mira activos."""
    _crear_cliente(db, "Ana")
    _crear_cliente(db, "Ana María")
    _crear_cliente(db, "Bruno")
    _crear_cliente(db, "Anabel", activo=False)

    nombres = [cliente.nombre for cliente in ClienteRepository(db).listar("AN")]

    assert nombres == ["Ana", "Ana María"]


def test_tiene_mascotas_es_verdadero_si_hay_una(db: Session) -> None:
    """tiene_mascotas consulta la tabla mascota por cliente_id."""
    cliente = _crear_cliente(db)
    especie = Especie(nombre="PERRO")
    db.add(especie)
    db.flush()
    db.add(
        Mascota(
            cliente_id=cliente.id,
            especie_id=especie.id,
            nombre="Luna",
            fecha_nacimiento=date(2020, 1, 1),
        )
    )
    db.commit()

    assert ClienteRepository(db).tiene_mascotas(cliente.id) is True


def test_tiene_mascotas_ignora_las_inactivas(db: Session) -> None:
    """Una mascota dada de baja ya no cuenta para bloquear al cliente."""
    cliente = _crear_cliente(db)
    especie = Especie(nombre="PERRO")
    db.add(especie)
    db.flush()
    db.add(
        Mascota(
            cliente_id=cliente.id,
            especie_id=especie.id,
            nombre="Luna",
            fecha_nacimiento=date(2020, 1, 1),
            activo=False,
        )
    )
    db.commit()

    assert ClienteRepository(db).tiene_mascotas(cliente.id) is False


def test_tiene_mascotas_es_falso_sin_mascotas_propias(db: Session) -> None:
    """Las mascotas de otro cliente no cuentan."""
    con_mascota = _crear_cliente(db, "Ana")
    sin_mascota = _crear_cliente(db, "Bruno")
    especie = Especie(nombre="PERRO")
    db.add(especie)
    db.flush()
    db.add(
        Mascota(
            cliente_id=con_mascota.id,
            especie_id=especie.id,
            nombre="Luna",
            fecha_nacimiento=date(2020, 1, 1),
        )
    )
    db.commit()

    assert ClienteRepository(db).tiene_mascotas(sin_mascota.id) is False
