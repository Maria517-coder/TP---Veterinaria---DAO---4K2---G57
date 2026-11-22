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

export function selectOpciones(items, { placeholder = "Seleccionar…", valor = "id", texto = "nombre" } = {}) {
  const select = document.createElement("select");
  const opcionVacia = document.createElement("option");
  opcionVacia.value = "";
  opcionVacia.textContent = placeholder;
  select.appendChild(opcionVacia);
  items.forEach((item) => {
    const opcion = document.createElement("option");
    opcion.value = String(item[valor]);
    opcion.textContent = String(item[texto]);
    select.appendChild(opcion);
  });
  return select;
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
      if (valor instanceof Node) {
        celda.appendChild(valor);
      } else {
        celda.textContent = valor === null || valor === undefined || valor === "" ? "—" : String(valor);
      }
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
