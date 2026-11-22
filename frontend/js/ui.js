/* Helpers de DOM: todo texto dinámico entra por textContent. */
export function crearElemento(etiqueta, texto = "", clase = "") {
  const nodo = document.createElement(etiqueta);
  if (texto !== null && texto !== undefined && texto !== "") {
    nodo.textContent = String(texto);
  }
  if (clase) nodo.className = clase;
  return nodo;
}

export function limpiar(nodo) {
  while (nodo.firstChild) nodo.removeChild(nodo.firstChild);
}

export function campo(etiqueta, control, id) {
  const envoltorio = crearElemento("div", "", "campo");
  const label = crearElemento("label", etiqueta);
  if (id) {
    control.id = id;
    label.htmlFor = id;
  }
  envoltorio.appendChild(label);
  envoltorio.appendChild(control);
  return envoltorio;
}

export function entradaTexto(placeholder = "", tipo = "text") {
  const entrada = document.createElement("input");
  entrada.type = tipo;
  entrada.placeholder = placeholder;
  return entrada;
}

export function entradaArea(placeholder = "") {
  const area = document.createElement("textarea");
  area.placeholder = placeholder;
  return area;
}

export function llenarSelect(select, items, { placeholder = "Seleccionar…", valor = "id", texto = "nombre", incluirVacio = true } = {}) {
  limpiar(select);
  if (incluirVacio) {
    const opcionVacia = document.createElement("option");
    opcionVacia.value = "";
    opcionVacia.textContent = placeholder;
    select.appendChild(opcionVacia);
  }
  items.forEach((item) => {
    const opcion = document.createElement("option");
    opcion.value = String(typeof valor === "function" ? valor(item) : item[valor]);
    opcion.textContent = String(typeof texto === "function" ? texto(item) : item[texto]);
    select.appendChild(opcion);
  });
  return select;
}

export function selectOpciones(items, opciones = {}) {
  return llenarSelect(document.createElement("select"), items, opciones);
}

export function agregarBoton(contenedor, texto, alHacerClic, clase = "boton boton-principal") {
  const boton = crearElemento("button", texto, clase);
  boton.type = "button";
  boton.addEventListener("click", alHacerClic);
  contenedor.appendChild(boton);
  return boton;
}

export function tabla(encabezados, filas) {
  const contenedor = crearElemento("div", "", "tabla-contenedor");
  const resultado = crearElemento("table");
  const cabecera = crearElemento("thead");
  const filaCabecera = crearElemento("tr");
  encabezados.forEach((texto) => filaCabecera.appendChild(crearElemento("th", texto)));
  cabecera.appendChild(filaCabecera);
  resultado.appendChild(cabecera);

  const cuerpo = crearElemento("tbody");
  filas.forEach((fila) => {
    const filaTabla = crearElemento("tr");
    fila.forEach((valor) => {
      const celda = crearElemento("td");
      if (valor instanceof Node) celda.appendChild(valor);
      else celda.textContent = valor === null || valor === undefined || valor === "" ? "—" : String(valor);
      filaTabla.appendChild(celda);
    });
    cuerpo.appendChild(filaTabla);
  });
  resultado.appendChild(cuerpo);
  contenedor.appendChild(resultado);
  return contenedor;
}

export function mensaje(contenedor, texto, tipo = "info") {
  limpiar(contenedor);
  contenedor.appendChild(crearElemento("p", texto, `mensaje mensaje-${tipo}`));
}

export function textoOVacio(contenedor, texto) {
  limpiar(contenedor);
  contenedor.appendChild(crearElemento("p", texto, "vacio"));
}

export function etiquetaEstado(estado) {
  const valor = String(estado || "").trim();
  const clases = {
    Extraida: "estado estado-extraida",
    Empaquetada: "estado estado-empaquetada",
    EnTransito: "estado estado-en-transito",
    Recibida: "estado estado-recibida",
    Analizada: "estado estado-analizada",
    Rechazada: "estado estado-rechazada",
  };
  const textos = {
    Extraida: "Extraída",
    Empaquetada: "Empaquetada",
    EnTransito: "En tránsito",
    Recibida: "Recibida",
    Analizada: "Analizada",
    Rechazada: "Rechazada",
  };
  return crearElemento("span", textos[valor] || valor, clases[valor] || "estado");
}

export function etiquetaEstadoRemito(estado) {
  const valor = String(estado || "").trim();
  const clases = {
    GENERADO: "estado estado-generado",
    DESPACHADO: "estado estado-despachado",
    RECIBIDO: "estado estado-recibido-remito",
    CERRADO: "estado estado-cerrado",
  };
  return crearElemento("span", valor || "—", clases[valor] || "estado");
}

export function crearTarjeta(titulo, texto = "") {
  const tarjeta = crearElemento("section", "", "tarjeta");
  if (titulo) tarjeta.appendChild(crearElemento("h2", titulo));
  if (texto) tarjeta.appendChild(crearElemento("p", texto, "texto-secundario"));
  return tarjeta;
}

export function pestanas(definiciones, activaInicial) {
  const contenedor = crearElemento("div", "", "pestanas");
  const barra = crearElemento("div", "", "pestanas-barra");
  const panel = crearElemento("div", "", "pestanas-panel");
  let activa = activaInicial || (definiciones[0] && definiciones[0].id);

  async function mostrar(id) {
    activa = id;
    barra.querySelectorAll("button").forEach((boton) => {
      const esActiva = boton.dataset.id === id;
      boton.classList.toggle("activa", esActiva);
      boton.setAttribute("aria-selected", esActiva ? "true" : "false");
    });
    limpiar(panel);
    const def = definiciones.find((item) => item.id === id);
    if (def) await def.render(panel);
  }

  definiciones.forEach((def) => {
    const boton = crearElemento("button", def.titulo, "pestana");
    boton.type = "button";
    boton.dataset.id = def.id;
    boton.setAttribute("role", "tab");
    boton.addEventListener("click", () => {
      mostrar(def.id).catch((error) => mensaje(panel, error.message, "error"));
    });
    barra.appendChild(boton);
  });

  contenedor.appendChild(barra);
  contenedor.appendChild(panel);
  mostrar(activa).catch((error) => mensaje(panel, error.message, "error"));
  return contenedor;
}

export function formatearFechaHora(valor) {
  if (!valor) return "—";
  return String(valor).replace("T", " ").slice(0, 16);
}

export function vinculo(texto, hash, clase = "enlace") {
  const a = crearElemento("a", texto, clase);
  a.href = hash.startsWith("#") ? hash : `#${hash}`;
  return a;
}
