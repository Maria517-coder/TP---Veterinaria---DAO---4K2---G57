"""Tests directos del MascotaService, sin pasar por HTTP."""
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontrado
from app.models.cliente import Cliente
from app.models.especie import Especie
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.schemas.mascota import MascotaActualizar, MascotaCrear
from app.services.mascota_service import MascotaService


def _crear_cliente(db: Session, nombre: str = "Ana", activo: bool = True) -> Cliente:
    """Inserta un cliente ya confirmado para usarlo como dato de prueba."""
    cliente = Cliente(nombre=nombre, telefono="123", activo=activo)
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


def _datos(
    cliente: Cliente,
    especie: Especie,
    nombre: str = "Luna",
    fecha_nacimiento: date = date(2020, 1, 1),
) -> MascotaCrear:
    """Arma el schema de entrada con datos válidos."""
    return MascotaCrear(
        cliente_id=cliente.id,
        especie_id=especie.id,
        nombre=nombre,
        fecha_nacimiento=fecha_nacimiento,
    )


def test_crear_guarda_mascota_y_historia_en_la_misma_transaccion(
    db: Session,
) -> None:
    """crear confirma la mascota y su historia, con numero = id de la mascota."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)

    mascota = MascotaService(db).crear(_datos(cliente, especie, "  Luna  "))
    mascota_id = mascota.id

    assert mascota_id is not None
    assert mascota.nombre == "Luna"
    assert mascota.activo is True

    db.rollback()
    en_bd = db.get(Mascota, mascota_id)
    assert en_bd is not None
    historia = db.scalar(
        select(HistoriaClinica).where(HistoriaClinica.mascota_id == mascota_id)
    )
    assert historia is not None
    assert historia.numero == mascota_id


def test_crear_hace_rollback_si_falla_la_historia(db: Session, monkeypatch) -> None:
    """Si falla el guardado de la historia, no queda la mascota a medias."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    servicio = MascotaService(db)

    def fallar(historia: HistoriaClinica) -> None:
        raise RuntimeError("falla simulada")

    monkeypatch.setattr(servicio.repository, "guardar_historia", fallar)

    with pytest.raises(RuntimeError):
        servicio.crear(_datos(cliente, especie))

    assert db.scalars(select(Mascota)).all() == []


def test_crear_con_cliente_inexistente_lanza_recurso_no_encontrado(
    db: Session,
) -> None:
    """Un responsable que no existe se rechaza con 404 de dominio."""
    especie = _crear_especie(db)

    with pytest.raises(RecursoNoEncontrado):
        MascotaService(db).crear(
            MascotaCrear(
                cliente_id=9999,
                especie_id=especie.id,
                nombre="Luna",
                fecha_nacimiento=date(2020, 1, 1),
            )
        )


def test_crear_con_cliente_inactivo_lanza_recurso_no_encontrado(db: Session) -> None:
    """Un responsable dado de baja se comporta como inexistente."""
    cliente = _crear_cliente(db, activo=False)
    especie = _crear_especie(db)

    with pytest.raises(RecursoNoEncontrado):
        MascotaService(db).crear(_datos(cliente, especie))


def test_crear_con_especie_inexistente_lanza_recurso_no_encontrado(
    db: Session,
) -> None:
    """Una especie que no existe se rechaza con 404 de dominio."""
    cliente = _crear_cliente(db)

    with pytest.raises(RecursoNoEncontrado):
        MascotaService(db).crear(
            MascotaCrear(
                cliente_id=cliente.id,
                especie_id=9999,
                nombre="Luna",
                fecha_nacimiento=date(2020, 1, 1),
            )
        )


def test_listar_delega_los_filtros(db: Session) -> None:
    """listar acepta cliente_id y especie_id y solo devuelve activas."""
    ana = _crear_cliente(db, "Ana")
    bruno = _crear_cliente(db, "Bruno")
    perro = _crear_especie(db, "PERRO")
    gato = _crear_especie(db, "GATO")
    servicio = MascotaService(db)
    servicio.crear(_datos(ana, perro, "Luna"))
    servicio.crear(_datos(ana, gato, "Michi"))
    servicio.crear(_datos(bruno, perro, "Firulais"))

    nombres = [m.nombre for m in servicio.listar(cliente_id=ana.id, especie_id=perro.id)]

    assert nombres == ["Luna"]


def test_listar_por_cliente_valida_el_responsable(db: Session) -> None:
    """E06 lista solo las mascotas activas del cliente indicado."""
    ana = _crear_cliente(db, "Ana")
    bruno = _crear_cliente(db, "Bruno")
    especie = _crear_especie(db)
    servicio = MascotaService(db)
    servicio.crear(_datos(ana, especie, "Luna"))
    servicio.crear(_datos(bruno, especie, "Firulais"))

    nombres = [m.nombre for m in servicio.listar_por_cliente(ana.id)]

    assert nombres == ["Luna"]


def test_listar_por_cliente_inexistente_lanza_recurso_no_encontrado(
    db: Session,
) -> None:
    """E06 responde 404 si el cliente no existe."""
    with pytest.raises(RecursoNoEncontrado):
        MascotaService(db).listar_por_cliente(9999)


def test_listar_por_cliente_inactivo_lanza_recurso_no_encontrado(
    db: Session,
) -> None:
    """E06 responde 404 si el cliente está dado de baja."""
    cliente = _crear_cliente(db, activo=False)

    with pytest.raises(RecursoNoEncontrado):
        MascotaService(db).listar_por_cliente(cliente.id)


def test_obtener_devuelve_la_mascota(db: Session) -> None:
    """obtener devuelve el modelo cuando existe y está activa."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    servicio = MascotaService(db)
    creada = servicio.crear(_datos(cliente, especie))

    encontrada = servicio.obtener(creada.id)

    assert encontrada.id == creada.id


def test_obtener_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """obtener lanza RecursoNoEncontrado si el id no existe."""
    with pytest.raises(RecursoNoEncontrado):
        MascotaService(db).obtener(9999)


def test_obtener_inactiva_lanza_recurso_no_encontrado(db: Session) -> None:
    """Una mascota dada de baja se comporta como inexistente."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    servicio = MascotaService(db)
    creada = servicio.crear(_datos(cliente, especie))
    servicio.eliminar(creada.id)

    with pytest.raises(RecursoNoEncontrado):
        servicio.obtener(creada.id)


def test_actualizar_reemplaza_y_confirma(db: Session) -> None:
    """actualizar cambia los cuatro campos y hace commit."""
    ana = _crear_cliente(db, "Ana")
    bruno = _crear_cliente(db, "Bruno")
    perro = _crear_especie(db, "PERRO")
    gato = _crear_especie(db, "GATO")
    servicio = MascotaService(db)
    creada = servicio.crear(_datos(ana, perro, "Luna"))

    actualizada = servicio.actualizar(
        creada.id,
        MascotaActualizar(
            cliente_id=bruno.id,
            especie_id=gato.id,
            nombre="Luna María",
            fecha_nacimiento=date(2021, 2, 3),
        ),
    )
    mascota_id = actualizada.id

    assert actualizada.cliente_id == bruno.id
    assert actualizada.especie_id == gato.id
    assert actualizada.nombre == "Luna María"

    db.rollback()
    en_bd = db.get(Mascota, mascota_id)
    assert en_bd is not None
    assert en_bd.cliente_id == bruno.id
    assert en_bd.nombre == "Luna María"


def test_actualizar_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """actualizar lanza RecursoNoEncontrado si la mascota no existe."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)

    with pytest.raises(RecursoNoEncontrado):
        MascotaService(db).actualizar(
            9999,
            MascotaActualizar(
                cliente_id=cliente.id,
                especie_id=especie.id,
                nombre="Luna",
                fecha_nacimiento=date(2020, 1, 1),
            ),
        )


def test_actualizar_con_cliente_inexistente_lanza_recurso_no_encontrado(
    db: Session,
) -> None:
    """actualizar valida que el nuevo responsable exista y esté activo."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    servicio = MascotaService(db)
    creada = servicio.crear(_datos(cliente, especie))

    with pytest.raises(RecursoNoEncontrado):
        servicio.actualizar(
            creada.id,
            MascotaActualizar(
                cliente_id=9999,
                especie_id=especie.id,
                nombre="Luna",
                fecha_nacimiento=date(2020, 1, 1),
            ),
        )


def test_actualizar_con_especie_inexistente_lanza_recurso_no_encontrado(
    db: Session,
) -> None:
    """actualizar valida que la nueva especie exista."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    servicio = MascotaService(db)
    creada = servicio.crear(_datos(cliente, especie))

    with pytest.raises(RecursoNoEncontrado):
        servicio.actualizar(
            creada.id,
            MascotaActualizar(
                cliente_id=cliente.id,
                especie_id=9999,
                nombre="Luna",
                fecha_nacimiento=date(2020, 1, 1),
            ),
        )


def test_eliminar_hace_baja_logica_y_confirma(db: Session) -> None:
    """eliminar marca activo=False y hace commit, sin borrar la fila."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    servicio = MascotaService(db)
    creada = servicio.crear(_datos(cliente, especie))

    servicio.eliminar(creada.id)
    mascota_id = creada.id

    db.rollback()
    en_bd = db.get(Mascota, mascota_id)
    assert en_bd is not None
    assert en_bd.activo is False


def test_eliminar_inexistente_lanza_recurso_no_encontrado(db: Session) -> None:
    """eliminar lanza RecursoNoEncontrado si el id no existe."""
    with pytest.raises(RecursoNoEncontrado):
        MascotaService(db).eliminar(9999)


def test_eliminar_inactiva_lanza_recurso_no_encontrado(db: Session) -> None:
    """Una segunda baja de la misma mascota da 404."""
    cliente = _crear_cliente(db)
    especie = _crear_especie(db)
    servicio = MascotaService(db)
    creada = servicio.crear(_datos(cliente, especie))
    servicio.eliminar(creada.id)

    with pytest.raises(RecursoNoEncontrado):
        servicio.eliminar(creada.id)
