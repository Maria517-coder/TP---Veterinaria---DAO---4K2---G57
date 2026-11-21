"""E47: registrar el resultado cierra el remito cuando era la última muestra pendiente."""
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Cliente,
    ClinicaVeterinaria,
    Complejidad,
    ConsultaMedica,
    ContenedorEnvio,
    Especie,
    EstadoCatalogo,
    EstadoRemito,
    HistoriaClinica,
    Mascota,
    MuestraBiologica,
    RedVeterinaria,
    RemitoBiologico,
    TipoMuestra,
    Veterinario,
)
from app.schemas.muestra import ResultadoCrear
from app.seeds.datos_iniciales import cargar_datos_iniciales
from app.services.muestra_service import MuestraService


@pytest.fixture()
def ctx(db: Session) -> dict:
    """Contenedor con dos muestras Recibida y un remito RECIBIDO (fechas relativas)."""
    cargar_datos_iniciales(db)
    db.commit()
    red = db.scalar(select(RedVeterinaria))
    tipo = db.scalar(select(TipoMuestra).where(TipoMuestra.nombre == "SANGRE"))
    especie = db.scalar(select(Especie).where(Especie.nombre == "PERRO"))
    estados = {fila.nombre: fila for fila in db.scalars(select(EstadoCatalogo))}
    hoy = datetime.now().date()

    clinica = ClinicaVeterinaria(nombre="Centro", red=red)
    responsable = Cliente(nombre="Ana", telefono="123")
    db.add_all([clinica, responsable])
    db.flush()
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=hoy.replace(year=hoy.year - 3),
        responsable=responsable,
        especie=especie,
        historia_clinica=HistoriaClinica(numero=1),
    )
    veterinario = Veterinario(nombre="Eva", matricula="MP-E47", clinica=clinica)
    db.add_all([mascota, veterinario])
    db.flush()
    consulta = ConsultaMedica(
        numero=1,
        clinica=clinica,
        mascota=mascota,
        veterinario=veterinario,
        fecha=hoy,
        complejidad=Complejidad.BAJA,
        costo=Decimal("100.00"),
    )
    db.add(consulta)
    db.flush()

    contenedor = ContenedorEnvio(numero=1)
    db.add(contenedor)
    db.flush()
    muestras = []
    for _ in range(2):
        muestra = MuestraBiologica(
            consulta=consulta,
            tipo=tipo,
            estado_actual=estados["Extraida"],
            fecha=hoy,
        )
        db.add(muestra)
        db.flush()
        contenedor.agregar_muestra(muestra, "Eva")
        muestras.append(muestra.id)

    remito = contenedor.generar_remito("Lab Central", 1)
    db.add(remito)
    db.flush()
    remito.despachar("Eva")
    remito.registrar_recepcion("Luis")
    db.commit()
    assert remito.estado is EstadoRemito.RECIBIDO

    return {
        "db": db,
        "remito_id": remito.id,
        "m1": muestras[0],
        "m2": muestras[1],
    }


def test_registrar_resultado_no_cierra_si_otra_muestra_sigue_recibida(
    ctx: dict,
) -> None:
    db: Session = ctx["db"]
    servicio = MuestraService(db)

    actualizada = servicio.registrar_resultado(
        ctx["m1"], ResultadoCrear(texto="Negativo", responsable="Luis")
    )
    remito = db.get(RemitoBiologico, ctx["remito_id"])
    db.refresh(remito)

    assert actualizada.estado.nombre == "Analizada"
    assert remito.estado is EstadoRemito.RECIBIDO


def test_registrar_resultado_cierra_el_remito_con_la_ultima_muestra(ctx: dict) -> None:
    db: Session = ctx["db"]
    servicio = MuestraService(db)
    datos = ResultadoCrear(texto="Negativo", responsable="Luis")

    servicio.registrar_resultado(ctx["m1"], datos)
    servicio.registrar_resultado(ctx["m2"], datos)

    remito = db.get(RemitoBiologico, ctx["remito_id"])
    db.refresh(remito)
    assert remito.estado is EstadoRemito.CERRADO
