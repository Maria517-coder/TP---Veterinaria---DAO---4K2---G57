"""Reglas propias de ConsultaMedica: muestras e imprimibles."""
from datetime import date, datetime, timedelta

from app.models.complejidad import Complejidad
from app.models.consulta_medica import ConsultaMedica
from app.models.muestra_biologica import MuestraBiologica
from app.models.tipo_muestra import TipoMuestra


def _consulta(muestras: list[MuestraBiologica] | None = None) -> ConsultaMedica:
    return ConsultaMedica(
        numero=1,
        fecha=datetime.now().date() - timedelta(days=1),
        complejidad=Complejidad.MEDIA,
        costo="100.00",
        muestras=muestras or [],
    )


def test_tiene_muestras() -> None:
    assert _consulta().tiene_muestras() is False
    assert _consulta([MuestraBiologica(fecha=date.today())]).tiene_muestras() is True


def test_registrar_muestra_crea_extraida_y_primer_cambio() -> None:
    consulta = _consulta()
    tipo = TipoMuestra(nombre="SANGRE", costo_analisis="1500.00")

    muestra = consulta.registrar_muestra(tipo, "Dra. Eva")

    assert muestra in consulta.muestras
    assert muestra.tipo is tipo
    assert muestra.fecha == consulta.fecha
    assert muestra.estado_actual.nombre == "Extraida"
    assert len(muestra.historial) == 1
    assert muestra.historial[0].estado.nombre == "Extraida"
    assert muestra.historial[0].responsable == "Dra. Eva"
    assert isinstance(muestra.historial[0].fecha_hora, datetime)


def test_orden_derivacion_es_pdf_no_vacio() -> None:
    consulta = _consulta()
    tipo = TipoMuestra(nombre="SANGRE", costo_analisis="1500.00")
    consulta.registrar_muestra(tipo, "Dra. Eva")

    contenido = consulta.emitir_orden_derivacion()

    assert isinstance(contenido, bytes)
    assert len(contenido) > 0
    assert contenido.startswith(b"%PDF")


def test_comprobante_es_pdf_con_y_sin_resultados() -> None:
    consulta = _consulta()
    tipo = TipoMuestra(nombre="SANGRE", costo_analisis="1500.00")
    sin_resultado = consulta.registrar_muestra(tipo, "Dra. Eva")

    contenido = consulta.imprimir_comprobante()
    assert isinstance(contenido, bytes)
    assert contenido.startswith(b"%PDF")

    sin_resultado.resultado = "Negativo"
    con_resultado = consulta.imprimir_comprobante()
    assert con_resultado.startswith(b"%PDF")
    assert len(con_resultado) > 0
