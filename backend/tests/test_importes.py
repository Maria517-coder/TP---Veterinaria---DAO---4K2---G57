"""Normalización monetaria y recuperación de centavos en SQLite."""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import Numeric
from sqlalchemy.orm import Session

from app.exceptions.errores import ReglaDeNegocioViolada
from app.models import (
    Cliente, ClinicaVeterinaria, Complejidad, ConsultaMedica, Especie,
    HistoriaClinica, Mascota, RedVeterinaria, TipoMuestra, Veterinario,
)


@pytest.mark.parametrize("modelo,campo", [
    (ConsultaMedica, "costo"), (TipoMuestra, "costo_analisis"),
])
@pytest.mark.parametrize("entrada,esperado", [
    ("0.1", "0.10"), ("1.005", "1.01"), ("2.675", "2.68"),
    (Decimal("2.674"), "2.67"), (0, "0.00"),
    ("9999999999.99", "9999999999.99"),
])
def test_normaliza_al_asignar(
    modelo: type, campo: str, entrada: Decimal | str | int, esperado: str,
) -> None:
    """Ambos atributos quedan normalizados antes de enviarlos a SQLite."""
    objeto = modelo(**{campo: entrada})
    importe = getattr(objeto, campo)
    assert isinstance(importe, Decimal)
    assert importe == Decimal(esperado)
    assert importe.as_tuple().exponent == -2


@pytest.mark.parametrize("modelo,campo", [
    (ConsultaMedica, "costo"), (TipoMuestra, "costo_analisis"),
])
@pytest.mark.parametrize("entrada", [
    "NaN", "sNaN", "Infinity", "-Infinity", "10000000000.00",
    "-10000000000.00", "9999999999.991", "no es un importe", 1.005,
])
def test_rechaza_importes_invalidos(modelo: type, campo: str, entrada: object) -> None:
    """No se aceptan floats, valores no finitos ni importes fuera de rango."""
    with pytest.raises(ReglaDeNegocioViolada):
        modelo(**{campo: entrada})


def test_redondeo_simetrico_sin_definir_regla_de_signo() -> None:
    """El redondeo técnico funciona para ambos signos, sin prohibir negativos."""
    from app.models.importes import normalizar_importe

    assert normalizar_importe("-1.005") == Decimal("-1.01")


def test_reasignacion_tambien_normaliza() -> None:
    """Actualizar un atributo usa la misma normalización que crearlo."""
    consulta = ConsultaMedica(costo="1.00")
    tipo = TipoMuestra(costo_analisis="1.00")
    consulta.costo = Decimal("2.675")
    tipo.costo_analisis = Decimal("1.005")
    assert consulta.costo == Decimal("2.68")
    assert tipo.costo_analisis == Decimal("1.01")


@pytest.mark.parametrize("modelo,campo", [
    (ConsultaMedica, "costo"), (TipoMuestra, "costo_analisis"),
])
def test_mapeo_numeric_del_der(modelo: type, campo: str) -> None:
    """Las columnas conservan la representación decimal definida en el DER."""
    tipo = modelo.__table__.c[campo].type
    assert isinstance(tipo, Numeric)
    assert (tipo.precision, tipo.scale, tipo.asdecimal) == (12, 2, True)


@pytest.fixture()
def consulta() -> ConsultaMedica:
    """Construye una consulta con sus referencias obligatorias."""
    clinica = ClinicaVeterinaria(nombre="Centro", red=RedVeterinaria(nombre="Red"))
    return ConsultaMedica(
        numero=1, fecha=date(2026, 1, 1), complejidad=Complejidad.BAJA,
        clinica=clinica,
        veterinario=Veterinario(nombre="Eva", matricula="1", clinica=clinica),
        mascota=Mascota(
            nombre="Luna", fecha_nacimiento=date(2020, 1, 1),
            responsable=Cliente(nombre="Ana", telefono="123"),
            especie=Especie(nombre="PERRO"),
            historia_clinica=HistoriaClinica(numero=1),
        ),
    )


@pytest.mark.parametrize("entrada,esperado", [
    ("0.10", "0.10"), ("2.675", "2.68"),
    ("9999999999.98", "9999999999.98"),
    ("9999999999.99", "9999999999.99"),
])
def test_conserva_centavos_en_otra_sesion(
    db: Session, consulta: ConsultaMedica, entrada: str, esperado: str,
) -> None:
    """La conversión SQLite no cambia centavos dentro del rango permitido."""
    consulta.costo = entrada
    tipo = TipoMuestra(nombre="SANGRE", costo_analisis=entrada)
    db.add_all([consulta, tipo])
    db.commit()
    consulta_id, tipo_id = consulta.id, tipo.id
    with Session(bind=db.get_bind()) as otra:
        for importe in (
            otra.get(ConsultaMedica, consulta_id).costo,
            otra.get(TipoMuestra, tipo_id).costo_analisis,
        ):
            assert isinstance(importe, Decimal)
            assert importe == Decimal(esperado)
            assert importe.as_tuple().exponent == -2


def test_valores_por_defecto_decimales(db: Session, consulta: ConsultaMedica) -> None:
    """Los valores por defecto persistidos también son Decimal con dos decimales."""
    tipo = TipoMuestra(nombre="SANGRE")
    db.add_all([consulta, tipo])
    db.commit()
    assert str(consulta.costo) == "0.00"
    assert str(tipo.costo_analisis) == "0.00"
