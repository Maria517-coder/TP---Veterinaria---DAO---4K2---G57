"""Reportes de la red y facturación de una clínica."""
import flet as ft

from frontend.ui import Pantalla, campo, fila, seccion, selector, tabla

REPORTES = {
    "facturacion": "Facturación desglosada",
    "atenciones-derivaciones": "Atenciones y derivaciones",
    "muestras-rechazadas": "Muestras rechazadas",
    "vacunas-pendientes": "Vacunas pendientes",
    "tiempos-promedio": "Tiempos promedio",
}


def panel_reporte(p: Pantalla, clinica_id: int | None = None) -> ft.Control:
    """Presenta los filtros, las filas y los totales de un reporte."""
    tipo = selector("Reporte", [{"id": k, "nombre": v} for k, v in REPORTES.items()])
    tipo.value = "facturacion"
    tipo.visible = clinica_id is None
    clinica = selector("Clínica", [] if clinica_id else p.api.consultar("clinicas"), opcional=True)
    clinica.visible = clinica_id is None
    desde = campo("Desde (AAAA-MM-DD)")
    hasta = campo("Hasta (AAAA-MM-DD)")
    resultado = ft.Column()

    def generar() -> None:
        filtros = {"clinica_id": clinica_id or clinica.value}
        if tipo.value != "vacunas-pendientes":
            filtros.update(desde=desde.value, hasta=hasta.value)
        reporte = p.api.consultar(f"reportes/{tipo.value}", **filtros)
        resultado.controls = [ft.Text(reporte["titulo"], size=18), tabla(reporte["filas"]),
                              tabla([reporte["totales"]]) if reporte["totales"] else ft.Text("")]

    def cambiar(e: ft.Event) -> None:
        desde.visible = hasta.visible = tipo.value != "vacunas-pendientes"
        resultado.controls.clear()
        p.page.update()

    tipo.on_select = cambiar
    return seccion("Facturación" if clinica_id else "Generar reporte", fila(tipo, clinica, desde, hasta),
                   p.boton("Consultar facturación" if clinica_id else "Generar reporte", generar), resultado)


def reportes(p: Pantalla) -> None:
    """Muestra los cinco reportes disponibles para administración."""
    p.agregar(panel_reporte(p))
