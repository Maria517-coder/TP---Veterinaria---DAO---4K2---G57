"""Patrón Template Method: esqueleto común de todos los reportes."""
from abc import ABC, abstractmethod

from app.exceptions import ReglaDeNegocioViolada
from app.reportes.filtro_reporte import FiltroReporte
from app.reportes.resultado_reporte import ResultadoReporte


class Reporte(ABC):
    """Fija el orden de los pasos; las subclases solo consultan y calculan."""

    NOMBRES_TOTALES: tuple[str, ...] = ()
    """Nombres de los totales, en el mismo orden de ``ResultadoReporte.totales``."""

    def generar(self, filtro: FiltroReporte) -> ResultadoReporte:
        """Método plantilla: fija el orden de los pasos; no se sobreescribe."""
        self.validar_filtro(filtro)
        datos = self.obtener_datos(filtro)
        resultado = self.calcular(datos)
        return self.formatear(resultado)

    def validar_filtro(self, filtro: FiltroReporte) -> None:
        """Paso común: valida el rango y el id, sin consultar la base."""
        if (
            filtro.desde is not None
            and filtro.hasta is not None
            and filtro.desde > filtro.hasta
        ):
            raise ReglaDeNegocioViolada("'desde' no puede ser posterior a 'hasta'")
        if filtro.clinica_id is not None and filtro.clinica_id < 1:
            raise ReglaDeNegocioViolada("El id de clínica debe ser positivo")

    @abstractmethod
    def obtener_datos(self, filtro: FiltroReporte) -> list[object]:
        """Paso específico de cada reporte: consulta los datos."""

    @abstractmethod
    def calcular(self, datos: list[object]) -> ResultadoReporte:
        """Paso específico de cada reporte: agrega y calcula."""

    def formatear(self, resultado: ResultadoReporte) -> ResultadoReporte:
        """Paso común: entrega una copia para no compartir colecciones mutables."""
        return ResultadoReporte(
            titulo=resultado.titulo,
            filas=list(resultado.filas),
            totales=list(resultado.totales),
        )
