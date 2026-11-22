"""Helpers de DOM: todo texto dinámico entra por textContent."""
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

export function campo(etiqueta, control) {
  const envoltorio = crearElemento("label", "", "campo");
  envoltorio.appendChild(crearElemento("span", etiqueta, "campo-etiqueta"));
  envoltorio.appendChild(control);
  return envoltorio;
}

export function entradaTexto(placeholder = "", tipo = "text") {
  const entrada = document.createElement("input");
  entrada.type = tipo;
  entrada.placeholder = placeholder;
  return entrada;
}

export function agregarBoton(contenedor, texto, alHacerClic, clase = "boton") {
  const boton = crearElemento("button", texto, clase);
  boton.type = "button";
  boton.addEventListener("click", alHacerClic);
  contenedor.appendChild(boton);
  return boton;
}

export function tabla(encabezados, filas) {
  const resultado = crearElemento("table", "", "tabla");

  const cabecera = crearElemento("thead");
  const filaCabecera = crearElemento("tr");
  encabezados.forEach((texto) => filaCabecera.appendChild(crearElemento("th", texto)));
  cabecera.appendChild(filaCabecera);
  resultado.appendChild(cabecera);

  const cuerpo = crearElemento("tbody");
  filas.forEach((fila) => {
    const filaTabla = crearElemento("tr");
    fila.forEach((valor) => {
      const celda = crearElemento("td", valor === null || valor === undefined ? "—" : String(valor));
      filaTabla.appendChild(celda);
    });
    cuerpo.appendChild(filaTabla);
  });
  resultado.appendChild(cuerpo);
  return resultado;
}

export function mensaje(contenedor, texto, tipo = "info") {
  limpiar(contenedor);
  contenedor.appendChild(crearElemento("p", texto, `mensaje mensaje-${tipo}`));
}

export function textoOVacio(contenedor, texto) {
  limpiar(contenedor);
  contenedor.appendChild(crearElemento("p", texto, "vacio"));
}
