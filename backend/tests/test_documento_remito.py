from datetime import datetime
from types import SimpleNamespace

import pytest

from app.models.estado_remito import EstadoRemito
from app.reportes import documento_remito


@pytest.mark.parametrize("estado", list(EstadoRemito))
def test_pdf_muestra_el_valor_del_estado(
    monkeypatch: pytest.MonkeyPatch, estado: EstadoRemito
) -> None:
    remito = SimpleNamespace(
        numero=6,
        estado=estado,
        fecha_emision=datetime(2026, 11, 25, 11, 51),
        clinica_origen=None,
        clinica_origen_id=1,
        laboratorio_destino="Laboratorio Central",
        contenedor=SimpleNamespace(numero=7, precinto_intacto=True, muestras=[]),
        fecha_hora_despacho=None,
        fecha_hora_recepcion=None,
    )
    parrafos: list[str] = []
    paragraph_original = documento_remito.Paragraph

    def registrar_parrafo(texto: str, *args: object, **kwargs: object) -> object:
        parrafos.append(texto)
        return paragraph_original(texto, *args, **kwargs)

    monkeypatch.setattr(documento_remito, "Paragraph", registrar_parrafo)

    pdf = documento_remito.generar_remito(remito)

    assert pdf.startswith(b"%PDF-")
    [parrafo_estado] = [texto for texto in parrafos if texto.startswith("<b>Estado:</b>")]
    assert parrafo_estado == f"<b>Estado:</b> {estado.value}"
