"""Hash de contraseñas y tokens firmados HMAC (sin estado en base)."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from app.exceptions.errores import NoAutenticado

CLAVE_SECRETA = os.getenv("SECRET_KEY", "dev-secret-cambiar-en-produccion")
_ITERACIONES = 100_000
_LARGO_SAL = 16
_LARGO_HASH = 32
_VENCIMIENTO_DEFECTO = 8 * 60 * 60  # 8 horas


def _b64url_encode(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _b64url_decode(texto: str) -> bytes:
    padding = "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode(texto + padding)


def hashear_contrasena(contrasena: str) -> str:
    """Genera hash pbkdf2_hmac con sal aleatoria. Nunca devuelve la contraseña."""
    sal = secrets.token_bytes(_LARGO_SAL)
    derivado = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, _ITERACIONES, dklen=_LARGO_HASH)
    return f"pbkdf2_sha256${_ITERACIONES}${_b64url_encode(sal)}${_b64url_encode(derivado)}"


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    """Compara en tiempo constante usando hmac.compare_digest."""
    try:
        algoritmo, iteraciones_txt, sal_b64, hash_b64 = hash_guardado.split("$", 3)
        if algoritmo != "pbkdf2_sha256":
            return False
        iteraciones = int(iteraciones_txt)
        sal = _b64url_decode(sal_b64)
        esperado = _b64url_decode(hash_b64)
    except Exception:
        return False
    calculado = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), sal, iteraciones, dklen=len(esperado))
    return hmac.compare_digest(calculado, esperado)


def crear_token(datos: dict, vencimiento_segundos: int = _VENCIMIENTO_DEFECTO) -> str:
    """Crea un token firmado HMAC con id, rol y vencimiento."""
    payload = dict(datos)
    payload["exp"] = int(time.time()) + vencimiento_segundos
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)
    firma = hmac.new(CLAVE_SECRETA.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64url_encode(firma)}"


def decodificar_token(token: str) -> dict:
    """Valida firma y vencimiento; lanza NoAutenticado ante cualquier problema."""
    try:
        payload_b64, firma_b64 = token.split(".", 1)
    except ValueError:
        raise NoAutenticado("Token inválido o ausente") from None

    firma_esperada = hmac.new(CLAVE_SECRETA.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    try:
        firma_recibida = _b64url_decode(firma_b64)
    except Exception:
        raise NoAutenticado("Token inválido o ausente") from None

    if not hmac.compare_digest(firma_esperada, firma_recibida):
        raise NoAutenticado("Token inválido o ausente")

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        raise NoAutenticado("Token inválido o ausente") from None

    exp = payload.get("exp")
    if not isinstance(exp, int) or int(time.time()) >= exp:
        raise NoAutenticado("Token inválido o ausente")

    return payload
