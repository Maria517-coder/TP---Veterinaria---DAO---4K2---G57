"""Consultas y guardado de consultas médicas en el repository."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.complejidad import Complejidad
from app.models.consulta_medica import ConsultaMedica
from app.models.especie import Especie
from app.models.estado_catalogo import EstadoCatalogo
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.models.muestra_biologica import MuestraBiologica
from app.models.red_veterinaria import RedVeterinaria
from app.models.tipo_muestra import TipoMuestra
from app.models.veterinario import Veterinario
from app.repositories.consulta_repository import ConsultaRepository


@pytest.fixture()
def ctx(db: Session) -> dict:
    """Dos clínicas, dos veterinarios y dos mascotas para probar filtros."""
    red = RedVeterinaria(nombre="Red R")
    db.add(red)
    db.flush()
    centro = ClinicaVeterinaria(nombre="Centro", red=red)
    norte = ClinicaVeterinaria(nombre="Norte", red=red)
    db.add_all([centro, norte])
    db.flush()
    eva = Veterinario(nombre="Eva", matricula="MP-R1", clinica=centro)
    luis = Veterinario(nombre="Luis", matricula="MP-R2", clinica=norte)
    especie = Especie(nombre="PERRO-R")
    cliente = Cliente(nombre="Ana", telefono="123")
    db.add_all([eva, luis, especie, cliente])
    db.flush()
    nacimiento = datetime.now().date() - timedelta(days=365)
    luna = Mascota(
        nombre="Luna", fecha_nacimiento=nacimiento, responsable=cliente,
        especie=especie, historia_clinica=HistoriaClinica(numero=101),
    )
    sol = Mascota(
        nombre="Sol", fecha_nacimiento=nacimiento, responsable=cliente,
        especie=especie, historia_clinica=HistoriaClinica(numero=102),
    )
    db.add_all([luna, sol])
    db.flush()
    tipo = TipoMuestra(nombre="SANGRE-R", costo_analisis="1500.00")
    db.add_all([tipo, EstadoCatalogo(nombre="Extraida")])
    db.commit()
    return {
        "centro": centro.id, "norte": norte.id,
        "eva": eva.id, "luis": luis.id,
        "luna": luna.id, "sol": sol.id,
        "tipo": tipo.id,
        "hoy": datetime.now().date(),
    }


def _nueva(db: Session, ctx: dict, numero: int, clinica: int, veterinario: int,
           mascota: int, fecha) -> ConsultaMedica:
    consulta = ConsultaMedica(
        numero=numero, clinica_id=clinica, veterinario_id=veterinario,
        mascota_id=mascota, fecha=fecha,
        complejidad=Complejidad.BAJA, costo="100.00",
    )
    db.add(consulta)
    return consulta


def _con_muestras(db: Session, ctx: dict) -> tuple[ConsultaMedica, ConsultaMedica, ConsultaMedica]:
    a = _nueva(db, ctx, 1, ctx["centro"], ctx["eva"], ctx["luna"], ctx["hoy"] - timedelta(days=1))
    b = _nueva(db, ctx, 2, ctx["centro"], ctx["eva"], ctx["luna"], ctx["hoy"] - timedelta(days=2))
    c = _nueva(db, ctx, 3, ctx["norte"], ctx["luis"], ctx["sol"], ctx["hoy"] - timedelta(days=1))
    db.flush()
    tipo = db.get(TipoMuestra, ctx["tipo"])
    a.registrar_muestra(tipo, "Dra. Eva")
    db.commit()
    return a, b, c


def test_siguiente_numero(db: Session, ctx: dict) -> None:
    repositorio = ConsultaRepository(db)

    assert repositorio.siguiente_numero() == 1
    _nueva(db, ctx, 1, ctx["centro"], ctx["eva"], ctx["luna"], ctx["hoy"])
    db.commit()
    assert repositorio.siguiente_numero() == 2
    _nueva(db, ctx, 2, ctx["centro"], ctx["eva"], ctx["luna"], ctx["hoy"])
    db.commit()
    assert repositorio.siguiente_numero() == 3


def test_buscar_por_id(db: Session, ctx: dict) -> None:
    a, _, _ = _con_muestras(db, ctx)

    assert ConsultaRepository(db).buscar_por_id(a.id).id == a.id
    assert ConsultaRepository(db).buscar_por_id(9999) is None


def test_listar_con_filtros_combinables(db: Session, ctx: dict) -> None:
    a, b, c = _con_muestras(db, ctx)
    repositorio = ConsultaRepository(db)
    ids = lambda lista: [consulta.id for consulta in lista]

    assert ids(repositorio.listar()) == [a.id, b.id, c.id]
    assert ids(repositorio.listar(clinica_id=ctx["centro"])) == [a.id, b.id]
    assert ids(repositorio.listar(fecha=ctx["hoy"] - timedelta(days=1))) == [a.id, c.id]
    assert ids(repositorio.listar(mascota_id=ctx["luna"])) == [a.id, b.id]
    assert ids(repositorio.listar(veterinario_id=ctx["eva"])) == [a.id, b.id]
    assert ids(repositorio.listar(con_muestras=True)) == [a.id]
    assert ids(repositorio.listar(con_muestras=False)) == [b.id, c.id]
    assert ids(repositorio.listar(
        clinica_id=ctx["centro"], fecha=ctx["hoy"] - timedelta(days=1), con_muestras=True
    )) == [a.id]


def test_guardar_hace_flush_sin_commit(db: Session, ctx: dict) -> None:
    repositorio = ConsultaRepository(db)
    consulta = _nueva(db, ctx, repositorio.siguiente_numero(), ctx["centro"],
                      ctx["eva"], ctx["luna"], ctx["hoy"])

    guardada = repositorio.guardar(consulta)

    assert guardada.id is not None
    db.rollback()
    assert db.get(ConsultaMedica, guardada.id) is None


def test_guardar_muestra_hace_flush_sin_commit(db: Session, ctx: dict) -> None:
    a, _, _ = _con_muestras(db, ctx)
    repositorio = ConsultaRepository(db)
    tipo = db.get(TipoMuestra, ctx["tipo"])
    muestra = a.registrar_muestra(tipo, "Dra. Eva")

    guardada = repositorio.guardar_muestra(muestra)

    assert guardada.id is not None
    db.rollback()
    assert db.get(MuestraBiologica, guardada.id) is None
