"""Operaciones que usan las pantallas más allá del acceso."""
import httpx
import pytest

from frontend.api import Api, ErrorApi


@pytest.mark.parametrize("metodo,estado,esperado", [
    ("POST", 201, {"id": 7}), ("DELETE", 204, None), ("GET", 200, b"%PDF-1.4"),
])
def test_operacion(metodo: str, estado: int, esperado: object) -> None:
    def responder(pedido: httpx.Request) -> httpx.Response:
        assert pedido.method == metodo
        if isinstance(esperado, bytes):
            return httpx.Response(estado, content=esperado, headers={"Content-Type": "application/pdf"})
        return httpx.Response(estado, json=esperado)

    with httpx.Client(base_url="http://test/api/", transport=httpx.MockTransport(responder)) as cliente:
        assert Api(cliente).pedir(metodo, "recurso") == esperado


def test_conflicto_de_turno_conserva_el_detalle() -> None:
    transporte = httpx.MockTransport(lambda _: httpx.Response(409, json={"detalle": "Turno superpuesto"}))
    with httpx.Client(base_url="http://test/api/", transport=transporte) as cliente:
        with pytest.raises(ErrorApi, match="409 - Turno superpuesto"):
            Api(cliente).pedir("POST", "veterinarios/1/turnos", {})
