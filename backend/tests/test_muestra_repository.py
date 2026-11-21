"""Consultas y guardado de muestras, sin reglas de negocio en el repositorio."""
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Cliente,
    ClinicaVeterinaria,
    Complejidad,
    ConsultaMedica,
    ContenedorEnvio,
    Especie,
    EstadoCatalogo,
    HistoriaClinica,
    Mascota,
    MuestraBiologica,
    RedVeterinaria,
    TipoMuestra,
    Veterinario,
)
from app.repositories.muestra_repository import MuestraRepository

NOMBRES_ESTADOS = (
    "Extraida",
    "Empaquetada",
    "EnTransito",
    "Recibida",
    "Analizada",
    "Rechazada",
)


@pytest.fixture()
def estados(db: Session) -> dict[str, EstadoCatalogo]:
    """Carga el catálogo de estados que necesita toda muestra."""
    catalogo = {nombre: EstadoCatalogo(nombre=nombre) for nombre in NOMBRES_ESTADOS}
    db.add_all(list(catalogo.values()))
    db.flush()
    return catalogo


def _crear_muestra(
    db: Session,
    estados: dict[str, EstadoCatalogo],
    numero: int,
    nombre_estado: str,
    nombre_clinica: str,
    numero_contenedor: int | None,
    fecha: date,
) -> MuestraBiologica:
    """Persiste una muestra con todo su contexto mínimo y devuelve el objeto."""
    # La red es única en el dominio: se reutiliza en todas las muestras del test.
    red = db.scalar(select(RedVeterinaria))
    if red is None:
        red = RedVeterinaria(nombre="Red única")
        db.add(red)
    clinica = db.scalar(
        select(ClinicaVeterinaria).where(ClinicaVeterinaria.nombre == nombre_clinica)
    )
    if clinica is None:
        clinica = ClinicaVeterinaria(nombre=nombre_clinica, red=red)
        db.add(clinica)
    mascota = Mascota(
        nombre=f"Mascota {numero}",
        fecha_nacimiento=date(2020, 1, 1),
        responsable=Cliente(nombre=f"Cliente {numero}", telefono=str(numero)),
        especie=Especie(nombre=f"ESPECIE{numero}"),
        historia_clinica=HistoriaClinica(numero=numero),
    )
    consulta = ConsultaMedica(
        numero=numero,
        clinica=clinica,
        mascota=mascota,
        veterinario=Veterinario(
            nombre=f"Veterinario {numero}", matricula=f"M{numero}", clinica=clinica
        ),
        fecha=fecha,
        complejidad=Complejidad.BAJA,
        costo=Decimal("100.00"),
    )
    contenedor = None
    if numero_contenedor is not None:
        contenedor = db.scalar(
            select(ContenedorEnvio).where(ContenedorEnvio.numero == numero_contenedor)
        )
        if contenedor is None:
            contenedor = ContenedorEnvio(numero=numero_contenedor)
            db.add(contenedor)
    muestra = MuestraBiologica(
        consulta=consulta,
        tipo=TipoMuestra(
            nombre=f"TIPO{numero}", costo_analisis=Decimal("10.00")
        ),
        estado_actual=estados[nombre_estado],
        contenedor=contenedor,
        fecha=fecha,
    )
    db.add(muestra)
    db.flush()
    return muestra


def test_buscar_por_id_devuelve_la_muestra_o_none(
    db: Session, estados: dict[str, EstadoCatalogo]
) -> None:
    """El repositorio devuelve objetos o None; no decide qué hacer si falta."""
    muestra = _crear_muestra(db, estados, 1, "Extraida", "Centro", None, date.today())
    repositorio = MuestraRepository(db)

    assert repositorio.buscar_por_id(muestra.id) is muestra
    assert repositorio.buscar_por_id(muestra.id + 999) is None


def test_listar_ordena_por_id_y_combina_todos_los_filtros(
    db: Session, estados: dict[str, EstadoCatalogo]
) -> None:
    """Los cuatro filtros son AND y el orden es estable por id."""
    hoy = datetime.now().date()
    ayer = hoy - timedelta(days=1)
    objetivo = _crear_muestra(db, estados, 1, "Recibida", "Centro", 10, hoy)
    otra_recibida = _crear_muestra(db, estados, 2, "Recibida", "Centro", 20, hoy)
    analizada = _crear_muestra(db, estados, 3, "Analizada", "Centro", 10, hoy)
    otra_clinica = _crear_muestra(db, estados, 4, "Recibida", "Otra", 10, hoy)
    otro_dia = _crear_muestra(db, estados, 5, "Recibida", "Centro", 10, ayer)
    repositorio = MuestraRepository(db)

    assert repositorio.listar() == [
        objetivo,
        otra_recibida,
        analizada,
        otra_clinica,
        otro_dia,
    ]
    assert repositorio.listar(estado="Recibida") == [
        objetivo,
        otra_recibida,
        otra_clinica,
        otro_dia,
    ]
    assert repositorio.listar(estado="Analizada") == [analizada]
    assert repositorio.listar(clinica_id=objetivo.consulta.clinica_id) == [
        objetivo,
        otra_recibida,
        analizada,
        otro_dia,
    ]
    assert repositorio.listar(contenedor_id=objetivo.contenedor.id) == [
        objetivo,
        analizada,
        otra_clinica,
        otro_dia,
    ]
    assert repositorio.listar(fecha=hoy) == [
        objetivo,
        otra_recibida,
        analizada,
        otra_clinica,
    ]
    assert repositorio.listar(
        estado="Recibida",
        clinica_id=objetivo.consulta.clinica_id,
        contenedor_id=objetivo.contenedor.id,
        fecha=hoy,
    ) == [objetivo]
    assert repositorio.listar(estado="Rechazada") == []


def test_guardar_hace_flush_y_no_commit(
    db: Session, estados: dict[str, EstadoCatalogo]
) -> None:
    """Guardar asigna el id dentro de la transacción, sin confirmarla."""
    repositorio = MuestraRepository(db)
    existente = _crear_muestra(
        db, estados, 99, "Extraida", "Centro", None, datetime.now().date()
    )
    muestra = MuestraBiologica(
        consulta=existente.consulta,
        tipo=existente.tipo,
        estado_actual=estados["Extraida"],
        fecha=datetime.now().date(),
    )

    guardada = repositorio.guardar(muestra)

    assert guardada is muestra
    assert guardada.id is not None

    db.rollback()
    assert db.scalar(select(func.count()).select_from(MuestraBiologica)) == 0
