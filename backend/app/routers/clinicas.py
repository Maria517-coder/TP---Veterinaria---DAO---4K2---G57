"""Rutas del módulo Red, clínicas, veterinarios y tipos de muestra.
Este módulo agrupa varios recursos: no tiene prefijo y las rutas se declaran completas."""
from fastapi import APIRouter

router = APIRouter(tags=["Clínicas"])

# Endpoints a implementar (ver docs/endpoints_veterinaria.xlsx):
# TODO GET /red  (RedVeterinaria)
# TODO POST /red/clinicas  (RedVeterinaria.agregarClinica())
# TODO GET /clinicas
# TODO GET /clinicas/{id}
# TODO PUT /clinicas/{id}
# TODO POST /clinicas/{id}/veterinarios  (Veterinario (alta))
# TODO GET /clinicas/{id}/veterinarios
# TODO PUT /veterinarios/{id}
# TODO DELETE /veterinarios/{id}
# TODO GET /tipos-muestra  (TipoMuestra)
# TODO POST /tipos-muestra  (TipoMuestra (alta))
# TODO PUT /tipos-muestra/{id}
