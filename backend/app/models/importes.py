"""Normalización común de los atributos monetarios del dominio."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext

from app.exceptions.errores import ReglaDeNegocioViolada

CENTAVO = Decimal("0.01")
MAXIMO_IMPORTE = Decimal("9999999999.99")


def normalizar_importe(valor: Decimal | str | int) -> Decimal:
    """Valida el rango de Numeric(12, 2) y redondea sin convertir desde float."""
    if isinstance(valor, bool) or not isinstance(valor, (Decimal, str, int)):
        raise ReglaDeNegocioViolada("El importe debe ser Decimal, cadena o entero; no float")
    try:
        importe = Decimal(valor)
    except InvalidOperation as error:
        raise ReglaDeNegocioViolada("El importe no es un número decimal válido") from error
    if not importe.is_finite():
        raise ReglaDeNegocioViolada("El importe debe ser finito")
    if importe.copy_abs() > MAXIMO_IMPORTE:
        raise ReglaDeNegocioViolada("El importe está fuera del rango de Numeric(12, 2)")
    # TODO: confirmar si el dominio admite importes negativos.
    with localcontext() as contexto:
        contexto.prec = 28
        return importe.quantize(CENTAVO, rounding=ROUND_HALF_UP)
