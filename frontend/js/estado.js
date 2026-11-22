/* Estado compartido y carga de catálogos. */
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
  veterinariosPorClinica: {},
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
  return estado;
}

export async function cargarVeterinarios(clinicaId) {
  if (!clinicaId) return [];
  const vets = await api(`/clinicas/${clinicaId}/veterinarios`);
  estado.veterinariosPorClinica[String(clinicaId)] = vets;
  return vets;
}

export async function cargarTodosVeterinarios() {
  const clinicas = estado.clinicas.length ? estado.clinicas : await api("/clinicas");
  estado.clinicas = clinicas;
  const entradas = await Promise.all(
    clinicas.map(async (clinica) => [String(clinica.id), await api(`/clinicas/${clinica.id}/veterinarios`)]),
  );
  estado.veterinariosPorClinica = Object.fromEntries(entradas);
  return estado.veterinariosPorClinica;
}

export function todosLosVeterinarios() {
  return Object.values(estado.veterinariosPorClinica).flat();
}

export function nombreEspecie(id) {
  const especie = ESPECIES.find((item) => item.id === Number(id));
  return especie ? especie.nombre : `Especie ${id}`;
}
