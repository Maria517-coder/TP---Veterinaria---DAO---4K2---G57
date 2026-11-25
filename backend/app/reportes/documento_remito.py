"""Presentación imprimible del remito biológico, con ReportLab (sin librerías nuevas)."""
from datetime import date, datetime
from io import BytesIO
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if TYPE_CHECKING:
    from app.models.remito_biologico import RemitoBiologico


def _valor(valor: object) -> str:
    """Escapa un valor para usarlo dentro de un párrafo de ReportLab."""
    return escape(str(valor)) if valor is not None else "-"


def _fecha(valor: date | datetime | None) -> str:
    """Formatea fechas y fechas-hora, tolerando datos todavía no cargados."""
    if valor is None:
        return "-"
    formato = "%d/%m/%Y %H:%M" if isinstance(valor, datetime) else "%d/%m/%Y"
    return valor.strftime(formato)


def generar_remito(remito: "RemitoBiologico") -> bytes:
    """Construye el remito imprimible con su precinto y el detalle de muestras."""
    salida = BytesIO()
    documento = SimpleDocTemplate(
        salida,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Remito biológico N.º {remito.numero}",
    )
    estilos = getSampleStyleSheet()
    contenedor = remito.contenedor
    precinto = "Intacto" if contenedor is not None and contenedor.precinto_intacto else "Roto"
    elementos = [
        Paragraph("Remito biológico", estilos["Title"]),
        Paragraph(f"Remito N.º {remito.numero}", estilos["Heading2"]),
        Paragraph(f"<b>Estado:</b> {_valor(remito.estado.value)}", estilos["BodyText"]),
        Paragraph(f"<b>Fecha de emisión:</b> {_fecha(remito.fecha_emision)}", estilos["BodyText"]),
        Paragraph(
            f"<b>Clínica de origen:</b> {_valor(remito.clinica_origen.nombre if remito.clinica_origen else remito.clinica_origen_id)}",
            estilos["BodyText"],
        ),
        Paragraph(
            f"<b>Laboratorio destino:</b> {_valor(remito.laboratorio_destino)}",
            estilos["BodyText"],
        ),
        Paragraph(
            f"<b>Contenedor:</b> N.º {_valor(contenedor.numero if contenedor else None)} "
            f"| <b>Precinto:</b> {precinto}",
            estilos["BodyText"],
        ),
        Paragraph(f"<b>Despacho:</b> {_fecha(remito.fecha_hora_despacho)}", estilos["BodyText"]),
        Paragraph(f"<b>Recepción:</b> {_fecha(remito.fecha_hora_recepcion)}", estilos["BodyText"]),
        Spacer(1, 8 * mm),
        Paragraph("Muestras transportadas", estilos["Heading2"]),
    ]

    filas = [["Tipo de muestra", "Estado", "Resultado"]]
    for muestra in contenedor.muestras if contenedor is not None else []:
        filas.append([
            _valor(muestra.tipo.nombre if muestra.tipo else None),
            _valor(muestra.estado_actual.nombre if muestra.estado_actual else None),
            _valor(muestra.resultado),
        ])
    tabla = Table(filas, colWidths=[55 * mm, 45 * mm, 65 * mm], repeatRows=1, hAlign="LEFT")
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24545C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#D8E2E4")),
    ]))
    elementos.append(tabla)
    documento.build(elementos)
    return salida.getvalue()
