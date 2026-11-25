"""Contrato entre el acceso Flet y la API de autenticación."""
import json

import httpx
import pytest

from frontend.api import Api, ErrorApi


def test_login_carga_perfil_y_descarta_token_vencido() -> None:
    def responder(pedido: httpx.Request) -> httpx.Response:
        if pedido.url.path == "/api/auth/login":
            assert pedido.method == "POST"
            assert json.loads(pedido.content) == {"usuario": "ana", "contrasena": "clave"}
            return httpx.Response(200, json={"token": "abc", "rol": "VETERINARIO", "veterinario_id": 2})
        assert pedido.headers["Authorization"] == "Bearer abc"
        if pedido.url.path == "/api/auth/yo":
            return httpx.Response(200, json={"clinica_id": 3})
        return httpx.Response(401)

    with httpx.Client(base_url="http://test/api/", transport=httpx.MockTransport(responder)) as cliente:
        api = Api(cliente)
        api.ingresar("ana", "clave")
        assert api.sesion.usuario == "ana"
        assert api.sesion.rol == "VETERINARIO"
        assert api.sesion.veterinario_id == 2
        assert api.sesion.clinica_id == 3
        with pytest.raises(ErrorApi, match="Sesión vencida"):
            api.consultar("clientes")
        assert api.sesion is None


def test_login_invalido_muestra_error_del_backend() -> None:
    def rechazar(pedido: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detalle": "Credenciales inválidas"})

    with httpx.Client(base_url="http://test/api/", transport=httpx.MockTransport(rechazar)) as cliente:
        api = Api(cliente)
        with pytest.raises(ErrorApi, match="Credenciales inválidas"):
            api.ingresar("ana", "incorrecta")
        assert api.sesion is None
