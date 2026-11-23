"""Tests del núcleo de seguridad: hash de contraseña y tokens HMAC."""
import time

import pytest

from app.core.seguridad import (
    crear_token,
    decodificar_token,
    hashear_contrasena,
    verificar_contrasena,
)
from app.exceptions.errores import NoAutenticado


def test_el_hash_no_es_la_contrasena_en_texto_plano() -> None:
    contrasena = "secreta123"
    hash_guardado = hashear_contrasena(contrasena)

    assert hash_guardado != contrasena
    assert "secreta123" not in hash_guardado


def test_verificar_contrasena_correcta_e_incorrecta() -> None:
    hash_guardado = hashear_contrasena("secreta123")

    assert verificar_contrasena("secreta123", hash_guardado) is True
    assert verificar_contrasena("otra-cosa", hash_guardado) is False


def test_el_hash_incluye_sal_y_no_es_determinista() -> None:
    a = hashear_contrasena("secreta123")
    b = hashear_contrasena("secreta123")

    assert a != b
    assert verificar_contrasena("secreta123", a)
    assert verificar_contrasena("secreta123", b)


def test_token_valido_devuelve_datos() -> None:
    token = crear_token({"id": 7, "rol": "ADMIN"}, vencimiento_segundos=3600)
    datos = decodificar_token(token)

    assert datos["id"] == 7
    assert datos["rol"] == "ADMIN"
    assert "exp" in datos


def test_token_alterado_da_401() -> None:
    token = crear_token({"id": 7, "rol": "ADMIN"}, vencimiento_segundos=3600)
    alterado = token[:-2] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(NoAutenticado):
        decodificar_token(alterado)


def test_token_vencido_da_401() -> None:
    token = crear_token({"id": 7, "rol": "ADMIN"}, vencimiento_segundos=-1)

    with pytest.raises(NoAutenticado):
        decodificar_token(token)


def test_token_mal_formado_da_401() -> None:
    with pytest.raises(NoAutenticado):
        decodificar_token("no-es-un-token")
