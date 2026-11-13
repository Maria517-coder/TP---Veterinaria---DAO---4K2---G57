"""Presentación del carnet de vacunas como PDF descargable."""
from io import BytesIO
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

if TYPE_CHECKING:
    from app.models.historia_clinica import HistoriaClinica


def generar_carnet(historia: "HistoriaClinica") -> bytes:
    """Construye el carnet con los datos y aplicaciones de la historia."""
    salida = BytesIO()
    documento = SimpleDocTemplate(
        salida, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title="Carnet de vacunación",
    )
    estilos = getSampleStyleSheet()
    mascota = historia.mascota
    responsable = mascota.responsable
    elementos = [
        Paragraph("Carnet de vacunación", estilos["Title"]),
        Paragraph(f"Historia clínica N.º {historia.numero}", estilos["Heading2"]),
        Paragraph(f"<b>Mascota:</b> {escape(mascota.nombre)}", estilos["BodyText"]),
        Paragraph(f"<b>Especie:</b> {escape(mascota.especie.nombre)}", estilos["BodyText"]),
        Paragraph(f"<b>Nacimiento:</b> {mascota.fecha_nacimiento:%d/%m/%Y}", estilos["BodyText"]),
        Paragraph(f"<b>Responsable:</b> {escape(responsable.nombre)}", estilos["BodyText"]),
        Paragraph(f"<b>Teléfono:</b> {escape(responsable.telefono)}", estilos["BodyText"]),
        Spacer(1, 8 * mm),
        Paragraph("Vacunas aplicadas", estilos["Heading2"]),
    ]
    filas = [["Fecha de aplicación", "Vacuna"]]
    for aplicacion in sorted(historia.aplicaciones, key=lambda registro: registro.fecha):
        filas.append([
            aplicacion.fecha.strftime("%d/%m/%Y"),
            Paragraph(escape(aplicacion.vacuna.nombre), estilos["BodyText"]),
        ])
    if historia.aplicaciones:
        tabla = Table(filas, colWidths=[45 * mm, 125 * mm], repeatRows=1, hAlign="LEFT")
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
    else:
        elementos.append(Paragraph("Sin vacunas registradas.", estilos["BodyText"]))
    documento.build(elementos)
    return salida.getvalue()
