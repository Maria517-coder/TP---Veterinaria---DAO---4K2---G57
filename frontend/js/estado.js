/*Estado compartido de la página y carga de catálogos.*/
import { api } from "./api.js";

// TODO: reemplazar por GET /api/especies cuando el backend exponga el catálogo.
// Hoy los seeds cargan estos ids en este orden (app/seeds/datos_iniciales.py).
export const ESPECIES = [
  { id: 1, nombre: "PERRO" },
  { id: 2, nombre: "GATO" },
  { id: 3, nombre: "OTRO" },
];

const estado = {
  red: null,
  clinicas: [],
  veterinarios: [],
  vacunas: [],
  tiposMuestra: [],
};

export function obtenerEstado() {
  return estado;
}

export async function cargarCatalogos() {
  const [red, clinicas, vacunas, tiposMuestra] = await Promise.all([
    api("/red"),
    api("/clinicas"),
    api("/vacunas"),
    api("/tipos-muestra"),
  ]);

  estado.red = red;
  estado.clinicas = clinicas;
  estado.vacunas = vacunas;
  estado.tiposMuestra = tiposMuestra;
  estado.veterinarios = [];
  return estado;
}

export async function cargarVeterinarios(clinicaId) {
  if (!clinicaId) {
    estado.veterinarios = [];
    return estado.veterinarios;
  }
  estado.veterinarios = await api(`/clinicas/${clinicaId}/veterinarios`);
  return estado.veterinarios;
}
