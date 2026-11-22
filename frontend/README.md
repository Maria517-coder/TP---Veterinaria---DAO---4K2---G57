# Frontend

Frontend mínimo en **HTML + JavaScript puro** (sin frameworks, sin librerías, sin npm), servido por FastAPI en `/app`.

## Cómo levantar

Desde la carpeta `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app
```

> **Importante:** no usar `--reload`. El modo reload puede interferir con la base SQLite durante la demo.

Luego abrir en el navegador:

- Frontend: `http://localhost:8000/app/`
- Swagger: `http://localhost:8000/docs`

Si el frontend se ve desactualizado, hacer recarga dura con **Ctrl+F5**.

## Estructura

- `index.html`: shell con sidebar y contenedor `#app`.
- `css/estilos.css`: estilos del diseño aprobado.
- `js/api.js`: envoltorio de fetch, manejo de errores y descarga de PDFs.
- `js/ui.js`: helpers de DOM (todo texto dinámico con `textContent`).
- `js/estado.js`: catálogos compartidos (especies hardcodeadas con TODO, clínicas, veterinarios, vacunas, tipos de muestra).
- `js/router.js`: router por hash (`#/ruta` y `#/ruta/:id`).
- `js/app.js`: registro de rutas y arranque.
- `js/vistas/`: una vista por área funcional.

## Flujo manual completo recomendado

1. **Clínica y veterinario**: ir a *Red y clínicas*, crear una clínica si hace falta, entrar a su ficha y agregar un veterinario.
2. **Cliente y mascota**: ir a *Recepción*, crear cliente y mascota (seleccionando cliente y especie).
3. **Consulta con muestra**: ir a *Consultorio*, completar clínica/veterinario/cliente/mascota, registrar consulta, revisar aviso de vacunas pendientes si corresponde, agregar una muestra y descargar PDFs si se necesita.
4. **Contenedor**: ir a *Laboratorio y envíos* → pestaña *Contenedores*, crear contenedor, entrar a su ficha y agregar la muestra Extraída indicando responsable.
5. **Remito**: desde la ficha del contenedor, generar remito indicando laboratorio destino.
6. **Despacho**: en la ficha del remito, ingresar responsable y despachar.
7. **Recepción**: en la ficha del remito despachado, ingresar responsable y registrar recepción. Si el precinto estaba roto, las muestras quedan Rechazadas.
8. **Resultado**: ir a *Laboratorio y envíos* → *Muestras*, abrir la muestra Recibida y registrar resultado con responsable.
9. **Reportes**: ir a *Reportes*, seleccionar cada reporte, aplicar filtros opcionales y generar para ver filas y totales.

## Notas

- Las especies están hardcodeadas en `js/estado.js` con un `TODO` hasta que el backend exponga `GET /api/especies`.
- Los turnos de una mascota se cargan bajo demanda con el botón “Cargar turnos”.
- Los errores del backend se muestran en español; los 409 de conflicto se muestran visibles en la pantalla.
