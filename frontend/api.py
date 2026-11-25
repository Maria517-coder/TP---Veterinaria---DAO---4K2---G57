"""Cliente de la API usado por una sesión de Flet."""
from dataclasses import dataclass

import httpx
from typing import Any


class ErrorApi(Exception):
    """Error que la pantalla puede mostrar al usuario."""


@dataclass
class Sesion:
    """Identidad y token del usuario conectado."""

    usuario: str
    token: str
    rol: str
    veterinario_id: int | None
    clinica_id: int | None = None


class Api:
    """Envía las credenciales de esta sesión al backend."""

    def __init__(self, cliente: httpx.Client) -> None:
        self.cliente = cliente
        self.sesion: Sesion | None = None

    def pedir(self, metodo: str, ruta: str, datos: dict | None = None,
              params: dict | None = None) -> Any:
        """Interpreta las respuestas JSON, PDF y sin contenido de FastAPI."""
        headers = {"Authorization": f"Bearer {self.sesion.token}"} if self.sesion else {}
        try:
            respuesta = self.cliente.request(metodo, ruta, json=datos, headers=headers, params=params)
        except httpx.RequestError as error:
            raise ErrorApi("No se pudo conectar con la API.") from error
        if respuesta.status_code == 401 and ruta != "auth/login":
            self.salir()
            raise ErrorApi("401 - Sesión vencida o inválida. Volvé a iniciar sesión.")
        if respuesta.is_error:
            try:
                cuerpo = respuesta.json()
            except ValueError:
                cuerpo = {}
            detalle = cuerpo.get("detalle") or cuerpo.get("detail") or "Error del servidor"
            if isinstance(detalle, list):
                detalle = "; ".join(item.get("msg", "Valor inválido") for item in detalle)
            raise ErrorApi(f"{respuesta.status_code} - {detalle}")
        if respuesta.status_code == 204:
            return None
        if "application/pdf" in respuesta.headers.get("content-type", ""):
            return respuesta.content
        return respuesta.json()

    def ingresar(self, usuario: str, contrasena: str) -> None:
        """Abre la sesión y obtiene la clínica asociada si está disponible."""
        self.salir()
        datos = self.pedir("POST", "auth/login", {"usuario": usuario, "contrasena": contrasena})
        self.sesion = Sesion(usuario.strip(), datos["token"], datos["rol"], datos.get("veterinario_id"))
        try:
            perfil = self.consultar("auth/yo")
        except ErrorApi:
            if self.sesion is None:
                raise
        else:
            self.sesion.clinica_id = perfil.get("clinica_id")

    def consultar(self, ruta: str, **filtros: object) -> Any:
        """Realiza una consulta autenticada."""
        return self.pedir("GET", ruta, params={k: v for k, v in filtros.items() if v not in (None, "")})

    def salir(self) -> None:
        """Descarta la identidad y el token."""
        self.sesion = None
