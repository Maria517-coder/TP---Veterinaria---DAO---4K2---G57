"""El historial permite inserciones y rechaza cambios desde ORM y SQLite."""
import sqlite3
from datetime import date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config.database import crear_tablas, engine
from app.models import (
    CambioEstado, Cliente, ClinicaVeterinaria, Complejidad, ConsultaMedica,
    Especie, EstadoCatalogo, HistoriaClinica, Mascota, MuestraBiologica,
    RedVeterinaria, TipoMuestra, Veterinario,
)


@pytest.fixture()
def cambio(db: Session) -> CambioEstado:
    """Persiste una muestra con su primer cambio y todas sus referencias."""
    clinica = ClinicaVeterinaria(nombre="Centro", red=RedVeterinaria(nombre="Red"))
    mascota = Mascota(
        nombre="Luna", fecha_nacimiento=date(2020, 1, 1),
        responsable=Cliente(nombre="Ana", telefono="123"),
        especie=Especie(nombre="PERRO"),
        historia_clinica=HistoriaClinica(numero=1),
    )
    consulta = ConsultaMedica(
        numero=1, clinica=clinica, mascota=mascota,
        veterinario=Veterinario(nombre="Eva", matricula="123", clinica=clinica),
        fecha=date(2026, 1, 1), complejidad=Complejidad.BAJA, costo=100,
    )
    estado = EstadoCatalogo(nombre="Extraida")
    muestra = MuestraBiologica(
        consulta=consulta, tipo=TipoMuestra(nombre="SANGRE", costo_analisis=100),
        estado_actual=estado, fecha=date(2026, 1, 1),
    )
    registro = CambioEstado(
        muestra=muestra, estado=estado,
        fecha_hora=datetime(2026, 1, 1, 10), responsable="Eva",
    )
    db.add(registro)
    db.commit()
    return registro


def test_permite_insertar_historial(db: Session, cambio: CambioEstado) -> None:
    """La protección no bloquea agregar nuevos registros históricos."""
    nuevo = CambioEstado(
        muestra=cambio.muestra, estado=cambio.estado,
        fecha_hora=datetime(2026, 1, 1, 11), responsable="Ana",
    )
    db.add(nuevo)
    db.commit()
    assert len(db.scalars(select(CambioEstado)).all()) == 2


@pytest.mark.parametrize("campo,valor", [
    ("responsable", "Otra persona"), ("fecha_hora", datetime(2026, 2, 1)),
    ("estado_id", 999), ("muestra_id", 999), ("id", 999),
])
def test_rechaza_actualizacion_orm(
    db: Session, cambio: CambioEstado, campo: str, valor: object,
) -> None:
    """Ningún atributo persistido de un cambio puede alterarse."""
    setattr(cambio, campo, valor)
    with pytest.raises(IntegrityError, match="historial inmutable"):
        db.flush()


def test_rechaza_eliminacion_orm(db: Session, cambio: CambioEstado) -> None:
    """Session.delete no puede eliminar un cambio histórico."""
    db.delete(cambio)
    with pytest.raises(IntegrityError, match="historial inmutable"):
        db.flush()


def test_quitar_de_coleccion_no_borra_historial(db: Session, cambio: CambioEstado) -> None:
    """Quitar un elemento no puede convertirlo en un huérfano borrable."""
    identificador = cambio.id
    cambio.muestra.historial.remove(cambio)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    assert db.get(CambioEstado, identificador) is not None


@pytest.mark.parametrize("cargar_historial", [True, False])
@pytest.mark.parametrize("borrar_consulta", [True, False])
def test_borrar_muestra_no_borra_historial(
    db: Session, cambio: CambioEstado, cargar_historial: bool, borrar_consulta: bool,
) -> None:
    """Ni borrar la muestra ni borrar su consulta puede llevarse el historial."""
    identificador = cambio.id
    muestra = cambio.muestra
    if cargar_historial:
        assert muestra.historial
    else:
        db.expire(muestra, ["historial"])
    db.delete(muestra.consulta if borrar_consulta else muestra)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    assert db.get(CambioEstado, identificador) is not None


@pytest.mark.parametrize("sentencia", [
    "UPDATE cambio_estado SET responsable = 'Otra persona' WHERE id = ?",
    "DELETE FROM cambio_estado WHERE id = ?",
    "INSERT OR REPLACE INTO cambio_estado SELECT * FROM cambio_estado WHERE id = ?",
    "REPLACE INTO cambio_estado SELECT * FROM cambio_estado WHERE id = ?",
])
def test_rechaza_sql_directo(cambio: CambioEstado, sentencia: str) -> None:
    """Una conexión sqlite3 ajena al ORM tampoco puede alterar el historial."""
    with sqlite3.connect(str(engine.url.database)) as conexion:
        with pytest.raises(sqlite3.IntegrityError, match="historial inmutable"):
            conexion.execute(sentencia, (cambio.id,))
        assert conexion.execute(
            "SELECT responsable FROM cambio_estado WHERE id = ?", (cambio.id,),
        ).fetchone() == ("Eva",)


def test_crear_tablas_reinstala_proteccion_existente(cambio: CambioEstado) -> None:
    """El arranque instala triggers también cuando la tabla ya existía."""
    with engine.begin() as conexion:
        nombres = conexion.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' "
            "AND tbl_name = 'cambio_estado'"
        ).scalars().all()
        for nombre in nombres:
            conexion.exec_driver_sql(f'DROP TRIGGER "{nombre}"')
    crear_tablas()
    crear_tablas()
    with sqlite3.connect(str(engine.url.database)) as conexion:
        with pytest.raises(sqlite3.IntegrityError, match="historial inmutable"):
            conexion.execute("DELETE FROM cambio_estado WHERE id = ?", (cambio.id,))
