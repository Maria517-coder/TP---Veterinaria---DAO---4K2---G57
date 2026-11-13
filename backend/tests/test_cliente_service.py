"""Tests directos del ClienteService, sin pasar por HTTP."""
from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso, RecursoNoEncontrado
from app.models.cliente import Cliente
from app.models.especie import Especie
from app.models.mascota import Mascota
from app.schemas.cliente import ClienteActualizar, ClienteCrear
from app.services.cliente_service import ClienteService


def _crear_cliente(db: Session, nombre: str = "Ana", activo: bool = True) -> Cliente:
    """Inserta un cliente ya confirmado para usarlo como dato de prueba."""
    cliente = Cliente(nombre=nombre, telefono="123", activo=activo)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def _agregar_mascota(db: Session, cliente: Cliente) -> None:
    """Inserta una mascota del cliente para disparar la regla de baja lógica."""
    especie = Especie(nombre=f"ESPECIE-{cliente.id}")
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


def test_crear_devuelve_el_modelo_y_confirma(db: Session) -> None:
    """crear guarda el cliente, hace commit y devuelve el modelo."""
    cliente = ClienteService(db).crear(ClienteCrear(nombre="  Ana  ", telefono=" 123 "))
    cliente_id = cliente.id

    assert cliente_id is not None
    assert cliente.nombre == "Ana"
    assert cliente.activo is True

    db.rollback()
    assert db.get(Cliente, cliente_id) is not None


def test_crear_hace_rollback_si_falla_el_guardado(db: Session, monkeypatch) -> None:
    """Si la persistencia falla, el service deshace la transacción."""
    servicio = ClienteService(db)
    repositorio = servicio.repository

    def guardar_y_fallar(cliente: Cliente) -> None:
        repositorio.db.add(cliente)
        repositorio.db.flush()
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(repositorio, "guardar", guardar_y_fallar)

    with pytest.raises(RuntimeError):
        servicio.crear(ClienteCrear(nombre="Ana", telefono="123"))

    assert db.scalar(select(func.count()).select_from(Cliente)) == 0


def test_listar_devuelve_solo_activos(db: Session) -> None:
    """listar delega en el repository y respeta la baja lógica."""
    _crear_cliente(db, "Ana")
    _crear_cliente(db, "Bruno", activo=False)

    nombres = [cliente.nombre for cliente in ClienteService(db).listar()]

    assert nombres == ["Ana"]


def test_listar_filtra_por_nombre(db: Session) -> None:
    """listar pasa el filtro al repository."""
    _crear_cliente(db, "Ana")
    _crear_cliente(db, "Bruno")

    nombres = [cliente.nombre for cliente in ClienteService(db).listar("br")]

    assert nombres == ["Bruno"]


def test_obtener_devuelve_el_cliente(db: Session) -> None:
    """obtener devuelve el modelo cuando existe y está activo."""
    cliente = _crear_cliente(db)

    encontrado = ClienteService(db).obtener(cliente.id)

    assert encontrado.id == cliente.id


def test_obtener_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """obtener lanza RecursoNoEncontrado si el id no existe."""
    with pytest.raises(RecursoNoEncontrado):
        ClienteService(db).obtener(9999)


def test_obtener_inactivo_lanza_recurso_no_encontrado(db: Session) -> None:
    """Un cliente dado de baja se comporta como inexistente."""
    cliente = _crear_cliente(db, activo=False)

    with pytest.raises(RecursoNoEncontrado):
        ClienteService(db).obtener(cliente.id)


def test_actualizar_reemplaza_y_confirma(db: Session) -> None:
    """actualizar cambia nombre y teléfono, hace commit y devuelve el modelo."""
    cliente = _crear_cliente(db)

    actualizado = ClienteService(db).actualizar(
        cliente.id, ClienteActualizar(nombre="Ana María", telefono="999")
    )
    cliente_id = actualizado.id

    assert actualizado.nombre == "Ana María"
    assert actualizado.telefono == "999"

    db.rollback()
    en_bd = db.get(Cliente, cliente_id)
    assert en_bd is not None
    assert en_bd.nombre == "Ana María"
    assert en_bd.telefono == "999"


def test_actualizar_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """actualizar lanza RecursoNoEncontrado si el id no existe."""
    with pytest.raises(RecursoNoEncontrado):
        ClienteService(db).actualizar(
            9999, ClienteActualizar(nombre="Ana", telefono="123")
        )


def test_eliminar_hace_baja_logica_y_confirma(db: Session) -> None:
    """eliminar marca activo=False y hace commit, sin borrar la fila."""
    cliente = _crear_cliente(db)

    ClienteService(db).eliminar(cliente.id)
    cliente_id = cliente.id

    db.rollback()
    en_bd = db.get(Cliente, cliente_id)
    assert en_bd is not None
    assert en_bd.activo is False


def test_eliminar_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """eliminar lanza RecursoNoEncontrado si el id no existe."""
    with pytest.raises(RecursoNoEncontrado):
        ClienteService(db).eliminar(9999)


def test_eliminar_inactivo_da_404_aunque_tenga_mascotas(db: Session) -> None:
    """Primero se controla la existencia: un inactivo da 404, no 409."""
    cliente = _crear_cliente(db, activo=False)
    _agregar_mascota(db, cliente)

    with pytest.raises(RecursoNoEncontrado):
        ClienteService(db).eliminar(cliente.id)


def test_eliminar_con_mascotas_lanza_conflicto_y_no_desactiva(db: Session) -> None:
    """Si tiene mascotas, el service lanza ConflictoDeRecurso y no toca al cliente."""
    cliente = _crear_cliente(db)
    _agregar_mascota(db, cliente)

    with pytest.raises(ConflictoDeRecurso):
        ClienteService(db).eliminar(cliente.id)

    assert db.get(Cliente, cliente.id).activo is True
