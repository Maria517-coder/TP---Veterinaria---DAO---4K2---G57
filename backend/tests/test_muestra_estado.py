"""Cambios de estado de una muestra: validación, historial y procesamiento."""
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.exceptions import ReglaDeNegocioViolada, TransicionInvalida
from app.models import (
    CambioEstado,
    Cliente,
    ClinicaVeterinaria,
    Complejidad,
    ConsultaMedica,
    Especie,
    EstadoCatalogo,
    HistoriaClinica,
    Mascota,
    MuestraBiologica,
    RedVeterinaria,
    TipoMuestra,
    Veterinario,
)
from app.models.estados import (
    Analizada,
    Empaquetada,
    EnTransito,
    Extraida,
    Rechazada,
    Recibida,
)

NOMBRES_ESTADOS = (
    "Extraida",
    "Empaquetada",
    "EnTransito",
    "Recibida",
    "Analizada",
    "Rechazada",
)


@pytest.fixture()
def muestra(db: Session) -> MuestraBiologica:
    """Persiste una muestra en Extraida con su catálogo de estados completo."""
    clinica = ClinicaVeterinaria(nombre="Centro", red=RedVeterinaria(nombre="Red"))
    mascota = Mascota(
        nombre="Luna",
        fecha_nacimiento=date(2020, 1, 1),
        responsable=Cliente(nombre="Ana", telefono="123"),
        especie=Especie(nombre="PERRO"),
        historia_clinica=HistoriaClinica(numero=1),
    )
    consulta = ConsultaMedica(
        numero=1,
        clinica=clinica,
        mascota=mascota,
        veterinario=Veterinario(nombre="Eva", matricula="123", clinica=clinica),
        fecha=date(2026, 1, 1),
        complejidad=Complejidad.BAJA,
        costo=Decimal("100.00"),
    )
    estados = {
        nombre: EstadoCatalogo(nombre=nombre) for nombre in NOMBRES_ESTADOS
    }
    db.add_all(list(estados.values()))
    objeto = MuestraBiologica(
        consulta=consulta,
        tipo=TipoMuestra(nombre="SANGRE", costo_analisis=Decimal("1500.00")),
        estado_actual=estados["Extraida"],
        fecha=date(2026, 1, 1),
    )
    db.add(objeto)
    db.commit()
    return objeto


def _fila_estado(db: Session, nombre: str) -> EstadoCatalogo:
    """Devuelve la fila del catálogo con ese nombre."""
    fila = db.scalar(select(EstadoCatalogo).where(EstadoCatalogo.nombre == nombre))
    assert fila is not None
    return fila


def test_cambiar_estado_valido_cambia_el_estado_y_registra_el_historial(
    db: Session, muestra: MuestraBiologica
) -> None:
    """Una transición válida actualiza el estado y agrega un CambioEstado completo."""
    muestra.cambiar_estado(Empaquetada(), "Eva")
    db.flush()

    assert muestra.estado_actual.nombre == "Empaquetada"
    assert isinstance(muestra.estado, Empaquetada)

    assert len(muestra.historial) == 1
    registro = muestra.historial[0]
    assert registro.muestra is muestra
    assert registro.muestra_id == muestra.id
    assert registro.estado is not None
    assert registro.estado.nombre == "Empaquetada"
    assert registro.estado_id == _fila_estado(db, "Empaquetada").id
    assert isinstance(registro.fecha_hora, datetime)
    assert registro.responsable == "Eva"


def test_cambiar_estado_no_hace_commit(db: Session, muestra: MuestraBiologica) -> None:
    """El modelo no confirma: si el llamador revierte, no queda nada."""
    muestra.cambiar_estado(Empaquetada(), "Eva")

    db.rollback()
    db.refresh(muestra)

    assert muestra.estado_actual.nombre == "Extraida"
    assert db.scalar(select(func.count()).select_from(CambioEstado)) == 0


def test_cambiar_estado_invalida_lanza_transicion_invalida_y_no_cambia_nada(
    db: Session, muestra: MuestraBiologica
) -> None:
    """Extraida no puede pasar directo a Recibida: ni estado ni historial cambian."""
    with pytest.raises(TransicionInvalida, match="Extraida.*Recibida"):
        muestra.cambiar_estado(Recibida(), "Eva")

    assert muestra.estado_actual.nombre == "Extraida"
    assert isinstance(muestra.estado, Extraida)
    assert muestra.historial == []

    db.flush()
    assert db.scalar(select(func.count()).select_from(CambioEstado)) == 0


def test_cambiar_estado_sin_sesion_lanza_un_error_claro() -> None:
    """Sin sesión no se puede registrar el historial: se avisa, no explota."""
    suelta = MuestraBiologica(
        estado_actual=EstadoCatalogo(nombre="Extraida"), fecha=date(2026, 1, 1)
    )

    with pytest.raises(ReglaDeNegocioViolada, match="sesión"):
        suelta.cambiar_estado(Empaquetada(), "Eva")


@pytest.mark.parametrize(
    "nombre,esperado",
    [
        ("Extraida", False),
        ("Empaquetada", False),
        ("EnTransito", False),
        ("Recibida", True),
        ("Analizada", False),
        ("Rechazada", False),
    ],
)
def test_puede_procesarse_solo_en_recibida(
    db: Session, muestra: MuestraBiologica, nombre: str, esperado: bool
) -> None:
    """Solo una muestra Recibida, llegada con precinto intacto, se procesa."""
    muestra.estado_actual = _fila_estado(db, nombre)
    db.flush()

    assert muestra.puede_procesarse() is esperado
