"""Controles compartidos por las pantallas Flet."""
from collections.abc import Callable, Iterable
from typing import Any

import flet as ft

from frontend.api import Api, ErrorApi


def campo(etiqueta: str, **opciones: Any) -> ft.TextField:
    """Construye un campo con su etiqueta visible."""
    return ft.TextField(label=etiqueta, width=270, **opciones)


def opciones(registros: Iterable[dict]) -> list[ft.DropdownOption]:
    """Usa el id para enviar el valor y el nombre para mostrarlo."""
    return [ft.DropdownOption(key=str(r["id"]), text=str(r.get("nombre", r["id"]))) for r in registros]


def selector(etiqueta: str, registros: Iterable[dict], opcional: bool = False) -> ft.Dropdown:
    """Presenta un catálogo, con opción de quitar el filtro cuando corresponde."""
    items = opciones(registros)
    if opcional:
        items.insert(0, ft.DropdownOption(key="", text="Todos"))
    return ft.Dropdown(label=etiqueta, options=items, width=270)


def requerido(control: ft.Control) -> str:
    """Obtiene el valor de un control obligatorio."""
    if not control.value:
        raise ErrorApi(f"Completá el campo {control.label}.")
    return str(control.value)


def fila(*controles: ft.Control) -> ft.Row:
    """Agrupa controles y permite que pasen a otra línea en pantallas angostas."""
    return ft.Row(list(controles), wrap=True, spacing=12, run_spacing=10)


def seccion(titulo: str, *controles: ft.Control) -> ft.Container:
    """Agrupa acciones y datos relacionados."""
    return ft.Container(content=ft.Column([ft.Text(titulo, size=19, weight=ft.FontWeight.BOLD),
                                           *controles], spacing=14),
                        padding=20, bgcolor=ft.Colors.SURFACE_CONTAINER_LOW, border_radius=14)


def legible(valor: Any) -> str:
    """Presenta campos anidados, estados booleanos y valores vacíos."""
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, list):
        return ", ".join(legible(item) for item in valor) or "—"
    if isinstance(valor, dict):
        return str(valor["nombre"]) if "nombre" in valor else " · ".join(
            f"{k.replace('_', ' ')}: {legible(v)}" for k, v in valor.items())
    return "—" if valor is None else str(valor)


def tabla(registros: list[dict], columnas: list[str] | None = None,
          accion: Callable | None = None) -> ft.Control:
    """Muestra una tabla desplazable con una acción opcional por registro."""
    if not registros:
        return ft.Text("Sin registros para esta selección.")
    claves = columnas or list(registros[0])
    titulos = [ft.DataColumn(ft.Text(k.replace("_", " ").capitalize())) for k in claves]
    if accion:
        titulos.append(ft.DataColumn(ft.Text("Acción")))
    filas = []
    for registro in registros:
        celdas = [ft.DataCell(ft.Text(legible(registro.get(k)), selectable=True)) for k in claves]
        if accion:
            celdas.append(ft.DataCell(accion(registro)))
        filas.append(ft.DataRow(cells=celdas))
    return ft.Row([ft.DataTable(columns=titulos, rows=filas)], scroll=ft.ScrollMode.AUTO)


class Pantalla:
    """Comparte navegación, avisos y manejo de errores de una página."""
    def __init__(self, page: ft.Page, api: Api) -> None:
        self.page = page
        self.api = api
        self.contenido = ft.Column(spacing=16)
        self.aviso = ft.Text("", color=ft.Colors.ERROR, selectable=True)
        self.titulo = ft.Text(size=30, weight=ft.FontWeight.BOLD)
        self.ruta = "/inicio"

    def agregar(self, *controles: ft.Control) -> None:
        """Agrega contenido al área actual."""
        self.contenido.controls.extend(controles)

    def ir(self, ruta: str) -> None:
        """Navega usando el historial del navegador."""
        self.page.run_task(self.page.push_route, ruta)

    def actualizar(self) -> None:
        """Recarga los datos de la ruta actual."""
        self.mostrar(self.ruta)

    def mostrar(self, ruta: str) -> None:
        """Construye la ruta elegida con el controlador de la aplicación."""
        raise NotImplementedError

    def error(self, error: ErrorApi) -> None:
        """Vuelve al formulario cuando vence la sesión."""
        if self.api.sesion is None and self.ruta != "/login":
            self.mostrar("/login")
        self.aviso.value = str(error)
        self.page.update()

    def boton(self, etiqueta: str, accion: Callable) -> ft.Button:
        """Ejecuta la acción y muestra los errores del backend."""
        def ejecutar(e: ft.Event) -> None:
            self.aviso.value = ""
            try:
                accion()
            except ErrorApi as error:
                self.error(error)
            self.page.update()

        return ft.Button(etiqueta, on_click=ejecutar)

    def enlace(self, etiqueta: str, ruta: str) -> ft.Button:
        """Abre un área o una ficha."""
        return self.boton(etiqueta, lambda: self.ir(ruta))

    def guardar(self, ruta: str, datos: dict, destino: str | None = None) -> None:
        """Guarda y refresca la vista o abre la ficha creada."""
        resultado = self.api.pedir("POST", ruta, datos)
        if destino:
            self.ir(f"/{destino}/{resultado['id']}")
        else:
            self.actualizar()

    def pdf(self, etiqueta: str, ruta: str, nombre: str) -> ft.Button:
        """Descarga el documento autenticado en el navegador."""
        async def descargar(e: ft.Event) -> None:
            try:
                datos = self.api.consultar(ruta)
                await ft.FilePicker().save_file(file_name=nombre, src_bytes=datos)
            except ErrorApi as error:
                self.error(error)

        return ft.Button(etiqueta, on_click=descargar)
