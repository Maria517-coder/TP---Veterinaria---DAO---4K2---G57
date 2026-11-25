# Cómo probar la rama `frontend-flet`

Esta rama incorpora una interfaz web en Python con Flet para que el equipo pueda evaluar los mismos recorridos de la veterinaria en dos interfaces. Ambas usan la misma API y la misma base SQLite.

## Arranque rápido en Windows con Git Bash

Desde la raíz del repositorio, con Python 3.11 o superior, traé la rama:

```bash
git fetch origin
git switch frontend-flet
```

**Solo la primera vez**, prepará los dos entornos. Flet usa una versión de FastAPI distinta para su propio servidor web.

```bash
python -m venv backend/.venv
./backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
python -m venv venv
./venv/Scripts/python.exe -m pip install -r frontend/requirements.txt
```

**Terminal 1 · API** (desde la raíz)

```bash
cd backend
./.venv/Scripts/python.exe -m uvicorn app.main:app
```

**Terminal 2 · Flet** (desde la raíz)

```bash
./venv/Scripts/python.exe -m frontend.main
```

Dejá abiertas ambas terminales y entrá a [la aplicación](http://localhost:8000/app/). En una instalación de desarrollo nueva, ingresá con `admin` y `admin123`, o con la clave configurada en `ADMIN_PASSWORD`. Para comparar una pantalla con la anterior, abrí la [interfaz clásica](http://localhost:8000/app/index.html). Para detener el sistema, usá Ctrl+C en cada terminal.

Si querés una base de ejemplo para recorrer las pantallas, desde `backend/` ejecutá `./.venv/Scripts/python.exe -m app.seeds.datos_demo` antes de iniciar los servidores. La demo incluye el veterinario `vet1` con clave `vet12345`.

## Qué cambió y dónde está

| Parte | Qué hace en esta rama | Archivo |
| --- | --- | --- |
| Entrada desde FastAPI | `/app/` redirige a Flet (puerto 8550 por defecto). `/app/index.html` sirve la versión clásica con sus recursos JS y CSS. | [backend/app/main.py](../backend/app/main.py) |
| Acceso y navegación | Presenta el login, el menú según el rol y las rutas de las áreas y fichas. El cierre de sesión descarta la identidad de esa página. | [frontend/main.py](../frontend/main.py) |
| Cliente HTTP | Envía el token a la API, consulta el perfil, interpreta errores y procesa respuestas JSON, PDF y bajas sin contenido. | [frontend/api.py](../frontend/api.py) |
| Controles compartidos | Define campos, selectores, tablas, enlaces, acciones de guardado y descarga de documentos en el navegador. | [frontend/ui.py](../frontend/ui.py) |
| Red y clínicas | Lista y ficha de sedes, alta y baja de clínicas, alta de veterinarios con acceso opcional, consultas y facturación por clínica. | [clinicas.py](../frontend/vistas/clinicas.py) |
| Recepción | Alta y búsqueda de mascotas y responsables, historia clínica, catálogo y aplicación de vacunas, carnet PDF, consultas y turnos de la mascota. | [recepcion.py](../frontend/vistas/recepcion.py) |
| Consultorio y turnos | Selección de profesional y paciente, agenda, disponibilidad, reserva y cancelación. Registro de atención, derivación de muestras, costo total, comprobante y orden en PDF. | [atencion.py](../frontend/vistas/atencion.py) |
| Laboratorio y envíos | Filtros de muestras y remitos, armado de contenedores, precintos, despacho, recepción, tiempo de tránsito, PDF de remito, historial y carga de resultados. | [laboratorio.py](../frontend/vistas/laboratorio.py) |
| Reportes | Cinco reportes de administración con filtros, filas y totales. La ficha de clínica reutiliza el panel de facturación. | [reportes.py](../frontend/vistas/reportes.py) |
| Entorno y configuración | Versiones de Flet, FastAPI para Flet y HTTPX. Las guías explican el arranque y cómo configurar las direcciones de los servidores. | [Dependencias](../frontend/requirements.txt), [guía del frontend](../frontend/README.md) y [README general](../README.md) |

## Cómo verificar los cambios

| Qué se prueba | Dónde |
| --- | --- |
| Login válido, credenciales rechazadas y token vencido | [test_sesion.py](../frontend/tests/test_sesion.py) |
| Altas, bajas sin contenido, respuestas PDF y conflictos de turno | [test_operaciones.py](../frontend/tests/test_operaciones.py) |
| Construcción de las áreas y restricción de reportes por rol | [test_pantallas.py](../frontend/tests/test_pantallas.py) |
| Redirección a Flet y acceso a la interfaz clásica y sus recursos | [test_frontend_base.py](../backend/tests/test_frontend_base.py) |

Para una revisión en el navegador con datos de demo, entrá como administrador, abrí una ficha de clínica, consultá la agenda de un veterinario y descargá el carnet desde la ficha de una mascota. Después ingresá como `vet1` y comprobá que la agenda corresponda a ese profesional y que el menú oculte Reportes.

## Antecedente de la base local

Durante la prueba con una SQLite antigua, Recepción abría y las otras cinco áreas fallaban al consultar `GET /api/clinicas`. A esa base le faltaba la columna `activo` en `clinica`, `veterinario` y `turno`. Se respaldó el archivo y se agregaron las columnas en una transacción. Después, el endpoint respondió `200` y las seis vistas pudieron cargar sus datos contra el servidor local. Una instalación con base nueva crea esas columnas desde los modelos.
