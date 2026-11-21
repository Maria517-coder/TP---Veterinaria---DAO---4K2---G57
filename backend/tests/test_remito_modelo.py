"""Ciclo de vida del RemitoBiologico y generación de su versión imprimible."""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import ConflictoDeRecurso
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
from app.models.estados import EnTransito, Rechazada, Recibida
from app.seeds.datos_iniciales import cargar_datos_iniciales


@pytest.fixture()
def ctx(db: Session) -> dict:
    """Prepara un contenedor con dos muestras Empaquetada y su remito GENERADO."""
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
    veterinario = Veterinario(nombre="Eva", matricula="MP-T2", clinica=clinica)
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=hoy - timedelta(days=365 * 3),
        responsable=responsable,
        especie=especie,
        historia_clinica=HistoriaClinica(numero=1),
    )
    db.add_all([veterinario, mascota])
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
    for _ in range(2):
        muestra = MuestraBiologica(
            consulta=consulta,
            tipo=tipo,
            estado_actual=estados["Extraida"],
            fecha=datetime.now().date(),
        )
        db.add(muestra)
        db.flush()
        contenedor.agregar_muestra(muestra, "Eva")
    remito = contenedor.generar_remito("Lab Central", 1)
    db.add(remito)
    db.commit()
    return {"db": db, "contenedor": contenedor, "remito": remito, "clinica": clinica}


def test_imprimir_devuelve_pdf(ctx: dict) -> None:
    pdf = ctx["remito"].imprimir()

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 100


def test_despachar_pasa_a_despachado_y_muestras_a_en_transito(ctx: dict) -> None:
    remito: RemitoBiologico = ctx["remito"]
    antes = datetime.now()

    remito.despachar("Eva")
    ctx["db"].flush()
    despues = datetime.now()

    assert remito.estado is EstadoRemito.DESPACHADO
    assert antes <= remito.fecha_hora_despacho <= despues
    assert all(isinstance(muestra.estado, EnTransito) for muestra in ctx["contenedor"].muestras)
    assert all(
        muestra.historial[-1].responsable == "Eva"
        and muestra.historial[-1].estado.nombre == "EnTransito"
        for muestra in ctx["contenedor"].muestras
    )

    with pytest.raises(ConflictoDeRecurso, match="GENERADO"):
        remito.despachar("Eva")


def test_recepcion_con_precinto_intacto_no_cierra(ctx: dict) -> None:
    remito: RemitoBiologico = ctx["remito"]
    remito.despachar("Eva")
    antes = datetime.now()

    remito.registrar_recepcion("Luis")
    ctx["db"].flush()

    assert remito.estado is EstadoRemito.RECIBIDO
    assert antes <= remito.fecha_hora_recepcion <= datetime.now()
    assert all(isinstance(muestra.estado, Recibida) for muestra in ctx["contenedor"].muestras)
    assert ctx["contenedor"].todas_muestras_finalizadas() is False


def test_recepcion_con_precinto_roto_cierra_en_cadena(ctx: dict) -> None:
    remito: RemitoBiologico = ctx["remito"]
    remito.despachar("Eva")
    ctx["contenedor"].romper_precinto()

    remito.registrar_recepcion("Luis")
    ctx["db"].flush()

    assert all(isinstance(muestra.estado, Rechazada) for muestra in ctx["contenedor"].muestras)
    assert remito.estado is EstadoRemito.CERRADO
    assert ctx["contenedor"].todas_muestras_finalizadas() is True
    assert remito.tiempo_transito() >= 0


def test_cerrar_solo_desde_recibido_y_tiempo_transito_requiere_fechas(ctx: dict) -> None:
    remito: RemitoBiologico = ctx["remito"]

    with pytest.raises(ConflictoDeRecurso, match="RECIBIDO"):
        remito.cerrar()
    with pytest.raises(ConflictoDeRecurso, match="despacho"):
        remito.tiempo_transito()

    remito.despachar("Eva")
    remito.fecha_hora_despacho = datetime.now() - timedelta(seconds=90)
    remito.registrar_recepcion("Luis")

    assert remito.tiempo_transito() == pytest.approx(90.0, abs=2.0)
