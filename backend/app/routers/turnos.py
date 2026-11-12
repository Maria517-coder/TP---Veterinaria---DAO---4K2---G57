"""Rutas del módulo Agenda y turnos.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from fastapi import APIRouter

router = APIRouter(tags=["Turnos"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO POST /veterinarios/{id}/turnos  (Agenda.agregarTurno())
# TODO GET /veterinarios/{id}/agenda
# TODO GET /veterinarios/{id}/turnos/disponibilidad  (Agenda.haySuperposicion())
# TODO DELETE /turnos/{id}
