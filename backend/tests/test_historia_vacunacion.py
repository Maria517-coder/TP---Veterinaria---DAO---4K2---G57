"""Reglas de vacunación de la historia clínica."""
from datetime import date

from app.models.historia_clinica import HistoriaClinica
from app.models.vacuna import Vacuna
from app.models.especie import Especie
from app.models.mascota import Mascota


def test_registrar_vacunacion_en_modelo() -> None:
    """La historia agrega la vacuna con su fecha de aplicación."""
    historia = HistoriaClinica()
    vacuna = Vacuna(nombre="Antirrábica")
    historia.registrar_vacunacion(vacuna, date(2026, 1, 1))
    assert len(historia.aplicaciones) == 1
    assert historia.aplicaciones[0].vacuna is vacuna
    assert historia.aplicaciones[0].fecha == date(2026, 1, 1)


def test_pendientes_descuenta_aplicadas_y_excluye_opcionales() -> None:
    """La regla conserva solo obligatorias de la especie aún sin aplicar."""
    aplicada = Vacuna(id=1, nombre="Aplicada", obligatoria=True)
    pendiente = Vacuna(id=2, nombre="Pendiente", obligatoria=True)
    opcional = Vacuna(id=3, nombre="Opcional", obligatoria=False)
    especie = Especie(nombre="PERRO")
    especie.vacunas = [aplicada, pendiente, opcional]
    historia = HistoriaClinica(mascota=Mascota(especie=especie))
    historia.registrar_vacunacion(aplicada, date(2026, 1, 1))
    assert historia.vacunas_pendientes() == [pendiente]
