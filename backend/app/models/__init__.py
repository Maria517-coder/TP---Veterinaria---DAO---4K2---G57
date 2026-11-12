"""Clases del dominio mapeadas con SQLAlchemy. Importarlas aquí las registra en Base.metadata."""
from app.models.aplicacion_vacuna import AplicacionVacuna
from app.models.cambio_estado import CambioEstado
from app.models.cliente import Cliente
from app.models.clinica_veterinaria import ClinicaVeterinaria
from app.models.complejidad import Complejidad
from app.models.consulta_medica import ConsultaMedica
from app.models.contenedor_envio import ContenedorEnvio
from app.models.especie import Especie
from app.models.estado_catalogo import EstadoCatalogo
from app.models.estado_remito import EstadoRemito
from app.models.historia_clinica import HistoriaClinica
from app.models.mascota import Mascota
from app.models.muestra_biologica import MuestraBiologica
from app.models.red_veterinaria import RedVeterinaria
from app.models.remito_biologico import RemitoBiologico
from app.models.tipo_muestra import TipoMuestra
from app.models.turno import Turno
from app.models.vacuna import Vacuna
from app.models.veterinario import Veterinario

__all__ = [
    "AplicacionVacuna", "CambioEstado", "Cliente", "ClinicaVeterinaria", "Complejidad",
    "ConsultaMedica", "ContenedorEnvio", "Especie", "EstadoCatalogo", "EstadoRemito",
    "HistoriaClinica", "Mascota", "MuestraBiologica", "RedVeterinaria", "RemitoBiologico",
    "TipoMuestra", "Turno", "Vacuna", "Veterinario",
]
