/* Inicio: tarjetas de acceso a las 6 áreas operativas. */
import { crearElemento, limpiar } from "../ui.js";

const AREAS = [
  {
    ruta: "#/clinicas",
    titulo: "Red y clínicas",
    descripcion: "Gestioná clínicas, veterinarios, consultas y facturación por clínica.",
  },
  {
    ruta: "#/recepcion",
    titulo: "Recepción",
    descripcion: "Buscá clientes y mascotas, consultá historias clínicas y vacunas.",
  },
  {
    ruta: "#/consultorio",
    titulo: "Consultorio",
    descripcion: "Registrá consultas paso a paso, muestras y documentos PDF.",
  },
  {
    ruta: "#/turnos",
    titulo: "Turnos",
    descripcion: "Consultá agendas, creá turnos, verificá disponibilidad y cancelá.",
  },
  {
    ruta: "#/laboratorio",
    titulo: "Laboratorio y envíos",
    descripcion: "Seguí muestras por estado, contenedores, remitos y resultados.",
  },
  {
    ruta: "#/reportes",
    titulo: "Reportes",
    descripcion: "Consultá los 5 reportes con filtros y revisá sus totales.",
  },
];

export async function montarInicio() {
  const app = document.getElementById("app");
  limpiar(app);

  const intro = crearElemento("section", "", "bloque-intro");
  intro.appendChild(crearElemento("h2", "Áreas de trabajo"));
  intro.appendChild(
    crearElemento(
      "p",
      "Elegí un área para comenzar. Cada pantalla te permite ver la lista, entrar al detalle y realizar acciones.",
      "texto-secundario",
    ),
  );
  app.appendChild(intro);

  const grilla = crearElemento("section", "", "grilla-tarjetas");
  AREAS.forEach((area) => {
    const tarjeta = crearElemento("a", "", "tarjeta tarjeta-enlace");
    tarjeta.href = area.ruta;
    tarjeta.appendChild(crearElemento("h3", area.titulo));
    tarjeta.appendChild(crearElemento("p", area.descripcion, "texto-secundario"));
    const accion = crearElemento("span", "Abrir área", "tarjeta-accion");
    accion.setAttribute("aria-hidden", "true");
    tarjeta.appendChild(accion);
    grilla.appendChild(tarjeta);
  });
  app.appendChild(grilla);
}
