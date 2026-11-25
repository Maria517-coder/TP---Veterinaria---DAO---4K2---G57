"""Render de cada área con catálogos vacíos y permisos reales de la interfaz."""
from unittest.mock import Mock

import flet as ft
import pytest

from frontend.api import Api, Sesion
from frontend.main import Aplicacion


@pytest.mark.parametrize("ruta,titulo", [
    ("inicio", "Áreas de trabajo"), ("clinicas", "Red y clínicas"),
    ("recepcion", "Recepción"), ("consultorio", "Consultorio"),
    ("turnos", "Turnos"), ("laboratorio", "Laboratorio y envíos"), ("reportes", "Reportes"),
])
def test_area_accesible_para_admin(ruta: str, titulo: str) -> None:
    api = Mock(spec=Api)
    api.sesion = Sesion("ana", "token", "ADMIN", None)
    api.consultar.return_value = []
    pagina = Mock(spec=ft.Page)
    app = Aplicacion(pagina, api)
    app.mostrar("/" + ruta)
    assert app.titulo.value == titulo
    assert app.contenido.controls
    assert not app.aviso.value


def test_veterinario_no_puede_abrir_reportes_por_url() -> None:
    api = Mock(spec=Api)
    api.sesion = Sesion("ana", "token", "VETERINARIO", 1)
    app = Aplicacion(Mock(spec=ft.Page), api)
    app.mostrar("/reportes")
    api.consultar.assert_not_called()
    assert "403" in app.aviso.value
