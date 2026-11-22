"""Arma la navegación y conecta la vista de preparación de datos."""
import { cargarCatalogos } from "./estado.js";
import { agregarBoton, limpiar, mensaje } from "./ui.js";
import { montarSetup } from "./vistas/setup.js";

function mostrarError(texto) {
  mensaje(document.getElementById("mensajes"), texto, "error");
}

async function iniciar() {
  const navegacion = document.getElementById("navegacion");
  limpiar(navegacion);
  const botonSetup = agregarBoton(navegacion, "Preparar datos", () => {}, "activo");
  botonSetup.disabled = true;

  mensaje(document.getElementById("mensajes"), "Cargando catálogos…", "info");

  try {
    const actualizarSetup = montarSetup({ mostrarError });
    await cargarCatalogos();
    await actualizarSetup();
    mensaje(
      document.getElementById("mensajes"),
      "Catálogos listos. Creá la clínica, el veterinario y las vacunas.",
      "ok",
    );
  } catch (error) {
    mostrarError(error.message);
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", iniciar);
} else {
  iniciar();
}
