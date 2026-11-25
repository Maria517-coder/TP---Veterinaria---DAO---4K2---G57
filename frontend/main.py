"""Aplicación web Flet de la red de clínicas veterinarias."""
import os

import flet as ft
import httpx

from frontend.api import Api, ErrorApi
from frontend.ui import Pantalla, campo, fila, seccion
from frontend.vistas import atencion, clinicas, laboratorio, recepcion, reportes

AREAS = {
    "clinicas": ("Red y clínicas", clinicas.clinicas),
    "recepcion": ("Recepción", recepcion.recepcion),
    "consultorio": ("Consultorio", atencion.consultorio),
    "turnos": ("Turnos", atencion.turnos),
    "laboratorio": ("Laboratorio y envíos", laboratorio.laboratorio),
    "reportes": ("Reportes", reportes.reportes),
}
FICHAS = {"clinicas": clinicas.ficha, "mascotas": recepcion.ficha, "consultas": atencion.ficha,
          "contenedores": laboratorio.contenedor, "remitos": laboratorio.remito, "muestras": laboratorio.muestra}


class Aplicacion(Pantalla):
    """Resuelve rutas y conserva una sesión independiente por página."""
    def mostrar(self, ruta: str) -> None:
        """Renderiza la vista pedida respetando el acceso del usuario."""
        self.ruta = ruta
        self.contenido.controls.clear()
        self.aviso.value = ""
        sesion = self.api.sesion
        cabecera = ft.Text("Red de clínicas veterinarias", size=17, weight=ft.FontWeight.BOLD)
        menu = fila(cabecera)
        self.titulo.value = "Iniciar sesión"
        if sesion:
            menu.controls.extend([self.enlace("Inicio", "/inicio"), ft.Text(f"{sesion.usuario} · {sesion.rol}"),
                                  self.boton("Cerrar sesión", self.salir)])
        self.page.controls.clear()
        self.page.add(ft.Column([menu, ft.Divider(), self.titulo, self.aviso, self.contenido], spacing=12))
        try:
            if not sesion:
                self.ruta = "/login"
                self.login()
            else:
                self.abrir(ruta)
        except ErrorApi as error:
            self.error(error)
        self.page.update()

    def abrir(self, ruta: str) -> None:
        """Selecciona el área o la ficha según los segmentos de la ruta."""
        partes = ruta.strip("/").split("/")
        area = partes[0]
        if area == "reportes" and self.api.sesion.rol != "ADMIN":
            self.titulo.value = "Reportes"
            raise ErrorApi("403 - Los reportes requieren el rol administrador.")
        if len(partes) == 2 and area in FICHAS and partes[1].isdigit():
            FICHAS[area](self, int(partes[1]))
        elif len(partes) == 1 and area in AREAS:
            self.titulo.value, vista = AREAS[area]
            vista(self)
        else:
            self.titulo.value = "Áreas de trabajo"
            self.agregar(fila(*(self.enlace(titulo, "/" + clave) for clave, (titulo, _) in AREAS.items()
                                if clave != "reportes" or self.api.sesion.rol == "ADMIN")))

    def login(self) -> None:
        """Presenta el formulario de acceso."""
        usuario = campo("Usuario", autofocus=True)
        clave = campo("Contraseña", password=True, can_reveal_password=True)

        def ingresar() -> None:
            self.api.ingresar(usuario.value or "", clave.value or "")
            if self.page.route == "/inicio":
                self.mostrar("/inicio")
            else:
                self.ir("/inicio")

        boton = self.boton("Ingresar", ingresar)
        clave.on_submit = boton.on_click
        self.agregar(seccion("Acceso", usuario, clave, boton))

    def salir(self) -> None:
        """Finaliza la sesión y muestra el formulario."""
        self.api.salir()
        self.mostrar("/login")
        self.ir("/login")


def main(page: ft.Page) -> None:
    """Configura el cliente HTTP y la navegación del navegador."""
    page.title = "Red de clínicas veterinarias"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.TEAL)
    page.padding = 24
    page.scroll = ft.ScrollMode.AUTO
    cliente = httpx.Client(base_url=os.getenv("VETERINARIA_API_URL", "http://127.0.0.1:8000/api/"))
    app = Aplicacion(page, Api(cliente))
    page.on_route_change = lambda e: app.mostrar(e.route)
    page.on_close = lambda e: cliente.close()
    app.mostrar(page.route or "/inicio")


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
