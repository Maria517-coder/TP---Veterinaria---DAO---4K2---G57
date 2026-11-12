"""Rutas del módulo Mascotas, historia clínica y vacunas.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from fastapi import APIRouter

router = APIRouter(tags=["Mascotas"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO POST /mascotas  (Mascota (alta))
# TODO GET /mascotas
# TODO GET /mascotas/{id}
# TODO PUT /mascotas/{id}
# TODO DELETE /mascotas/{id}
# TODO GET /mascotas/{id}/historia-clinica
# TODO GET /historias-clinicas/{id}/consultas
# TODO POST /vacunas  (Vacuna (alta))
# TODO GET /vacunas
# TODO POST /historias-clinicas/{id}/vacunaciones  (HistoriaClinica.registrarVacunacion())
# TODO GET /historias-clinicas/{id}/vacunaciones
# TODO GET /historias-clinicas/{id}/vacunas-pendientes  (HistoriaClinica.vacunasPendientes())
# TODO GET /mascotas/{id}/carnet-vacunas  (HistoriaClinica.imprimirCarnetVacunas())
