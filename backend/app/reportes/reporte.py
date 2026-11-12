"""Patrón Template Method: esqueleto común de todos los reportes."""
from abc import ABC, abstractmethod

from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.resultado_reporte import ResultadoReporte


class Reporte(ABC):
    def generar(self, filtro: FiltroReporte) -> ResultadoReporte:
        """Método plantilla: fija el orden de los pasos; no se sobreescribe."""
        self.validar_filtro(filtro)
        datos = self.obtener_datos(filtro)
        resultado = self.calcular(datos)
        return self.formatear(resultado)

    def validar_filtro(self, filtro: FiltroReporte) -> None:
        """Paso común. TODO: validar que desde <= hasta y que la clínica exista."""

    @abstractmethod
    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        """Paso específico de cada reporte: consulta los datos."""

    @abstractmethod
    def calcular(self, datos: list[object]) -> ResultadoReporte:
        """Paso específico de cada reporte: agrega y calcula."""

    def formatear(self, resultado: ResultadoReporte) -> ResultadoReporte:
        """Paso común. TODO: dar formato final al resultado."""
        return resultado
