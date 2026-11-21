"""Presentación imprimible de consultas: orden de derivación y comprobante.

Reutiliza el estilo del carnet de vacunas (ReportLab, A4, tabla con encabezado).
"""
from datetime import date
from io import BytesIO
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if TYPE_CHECKING:
    from app.models.consulta_medica import ConsultaMedica


def _valor(valor: object) -> str:
    """Escapa un valor de texto para usarlo en un párrafo de ReportLab."""
    return escape(str(valor)) if valor is not None else "-"


def _fecha(valor: date | None) -> str:
    """Formatea una fecha, tolerando datos todavía no cargados."""
    return valor.strftime("%d/%m/%Y") if valor is not None else "-"


def _documento(salida: BytesIO, titulo: str) -> SimpleDocTemplate:
    """Arma el documento con los mismos márgenes y estilo del carnet."""
    return SimpleDocTemplate(
        salida, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm, title=titulo,
    )


def _tabla(filas: list[list[str]], anchos: list[float]) -> Table:
    """Aplica el estilo de tabla usado en el carnet de vacunas."""
    tabla = Table(filas, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24545C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#D8E2E4")),
    ]))
    return tabla


def generar_orden_derivacion(consulta: "ConsultaMedica") -> bytes:
    """Construye la orden con las muestras que se derivan al laboratorio."""
    salida = BytesIO()
    documento = _documento(salida, "Orden de derivación")
    estilos = getSampleStyleSheet()
    mascota = consulta.mascota
    elementos = [
        Paragraph("Orden de derivación", estilos["Title"]),
        Paragraph(f"Consulta N.º {consulta.numero}", estilos["Heading2"]),
        Paragraph(f"<b>Fecha:</b> {_fecha(consulta.fecha)}", estilos["BodyText"]),
        Paragraph(
            f"<b>Mascota:</b> {_valor(mascota.nombre if mascota else None)}",
            estilos["BodyText"],
        ),
        Spacer(1, 8 * mm),
        Paragraph("Muestras a derivar", estilos["Heading2"]),
    ]
    filas = [["Tipo de muestra", "Fecha", "Estado"]]
    for muestra in consulta.muestras:
        filas.append([
            _valor(muestra.tipo.nombre if muestra.tipo else None),
            _fecha(muestra.fecha),
            _valor(muestra.estado_actual.nombre if muestra.estado_actual else None),
        ])
    elementos.append(_tabla(filas, [75 * mm, 45 * mm, 45 * mm]))
    documento.build(elementos)
    return salida.getvalue()


def generar_comprobante(consulta: "ConsultaMedica") -> bytes:
    """Construye el comprobante, con resultados solo si los hay."""
    salida = BytesIO()
    documento = _documento(salida, "Comprobante de atención")
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph("Comprobante de atención", estilos["Title"]),
        Paragraph(f"Consulta N.º {consulta.numero}", estilos["Heading2"]),
        Paragraph(f"<b>Fecha:</b> {_fecha(consulta.fecha)}", estilos["BodyText"]),
        Paragraph(f"<b>Complejidad:</b> {_valor(consulta.complejidad)}", estilos["BodyText"]),
        Paragraph(f"<b>Costo de la consulta:</b> {consulta.costo}", estilos["BodyText"]),
        Paragraph(f"<b>Costo total:</b> {consulta.costo_total()}", estilos["BodyText"]),
        Spacer(1, 8 * mm),
        Paragraph("Resultados", estilos["Heading2"]),
    ]
    con_resultado = [
        muestra for muestra in consulta.muestras if muestra.resultado
    ]
    if con_resultado:
        filas = [["Tipo de muestra", "Resultado"]]
        for muestra in con_resultado:
            filas.append([
                _valor(muestra.tipo.nombre if muestra.tipo else None),
                _valor(muestra.resultado),
            ])
        elementos.append(_tabla(filas, [70 * mm, 95 * mm]))
    else:
        elementos.append(
            Paragraph("Sin resultados registrados.", estilos["BodyText"])
        )
    documento.build(elementos)
    return salida.getvalue()
