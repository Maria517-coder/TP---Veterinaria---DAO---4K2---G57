# Proceso de historia clínica

## E12 — Consultar la historia clínica

Se trabaja en la rama `historia-clinica-vacunas`.
El endpoint es `GET /api/mascotas/{mascota_id}/historia-clinica`.
Devuelve los campos existentes del modelo `HistoriaClinica`: `id`, `mascota_id` y `numero`.
Las consultas de la historia tienen su propio endpoint previsto, E13.

### Preparación

Se deshabilitó temporalmente el import y registro del router de clínicas en
`backend/app/main.py`, porque faltan schemas y servicios que importa.
Con ese ajuste pasaron las 195 pruebas existentes y arrancó Uvicorn.
El router se debe volver a registrar cuando esté disponible el bloque A completo.

### Rojo

Se agregaron tres pruebas HTTP en `backend/tests/test_mascotas.py`.
Verifican una mascota existente, una inexistente y una dada de baja.
Las tres fallaron antes de implementar la ruta. El caso válido recibió 404.
Los otros dos recibieron el error genérico de ruta inexistente, con `detail`,
en lugar del error de dominio de la aplicación, con `detalle`.

### Implementación por capas

- El schema `HistoriaClinicaRespuesta` define los campos de salida y permite leer atributos del modelo.
- El servicio reutiliza `obtener()` y accede a la relación `historia_clinica`.
- El router recibe el identificador y delega en el servicio.
- Se reutiliza la búsqueda existente del repositorio, que filtra mascotas activas.

Se conserva así el criterio de las consultas actuales de mascotas: una mascota
inexistente o inactiva produce 404. La baja lógica conserva su historia en la base.
La historia se crea al dar de alta la mascota, por lo que este endpoint solamente la lee.

### Verificación

Desde `backend`, ejecutar `.\.venv\Scripts\python.exe -m pytest -q`.
Resultado: 198 pruebas pasaron en 54,88 segundos. Starlette emitió una advertencia
de deprecación sobre el uso de httpx en TestClient.
Se verificó con TestClient que `/docs` devuelve 200 y que `/openapi.json` incluye E12.
La implementación reutiliza el servicio y la relación existentes, sin duplicar consultas.

Para probar manualmente, iniciar `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload`,
abrir `http://127.0.0.1:8000/docs` y ejecutar E12 con el id de una mascota creada.
Debe devolver 200 con `id`, `mascota_id` y `numero`; un id inexistente devuelve 404.

## E13 a E18 — Consultas y vacunaciones

Se implementaron seis operaciones en cuatro tandas.

| Endpoint | Función |
| --- | --- |
| GET /api/historias-clinicas/{historia_id}/consultas | Consultas de la mascota asociada |
| POST /api/vacunas | Alta en el catálogo |
| GET /api/vacunas | Catálogo, con filtro opcional especie_id |
| POST /api/historias-clinicas/{historia_id}/vacunaciones | Registrar una aplicación |
| GET /api/historias-clinicas/{historia_id}/vacunaciones | Aplicaciones registradas |
| GET /api/historias-clinicas/{historia_id}/vacunas-pendientes | Obligatorias de la especie aún sin aplicar |

### Contratos y decisiones

El alta del catálogo recibe `nombre`, `obligatoria` (por defecto false, como el
modelo) y `especies_aplicables`, una lista de identificadores de especies.
La respuesta incluye cada especie con su id y nombre. Las especies repetidas
se vinculan una sola vez. Una especie inexistente devuelve 404 y un nombre
de vacuna duplicado devuelve 409, de acuerdo con la restricción única existente.

El registro de vacunación recibe `vacuna_id` y `fecha`. Devuelve el identificador
de la aplicación, el de la historia, el de la vacuna y la fecha. Una historia
o vacuna inexistente devuelve 404. El servicio revierte la transacción si falla
el guardado.

E13 devuelve los campos del modelo de consulta, incluyendo fecha, complejidad
y costo. Una historia sin consultas devuelve una lista vacía. Se comprueba que
las consultas de otra mascota queden excluidas.

La búsqueda directa por id de historia conserva el acceso a historias guardadas,
incluso si la mascota fue dada de baja. E12 sigue usando la consulta existente
de mascotas activas. Esta diferencia debe considerarse al probar ambos accesos.

### Responsabilidades

- Los schemas describen los cuerpos y respuestas.
- Los routers delegan en los servicios.
- Los repositorios consultan y guardan; los servicios confirman o revierten.
- `HistoriaClinica.registrar_vacunacion()` crea la aplicación.
- `HistoriaClinica.vacunas_pendientes()` aplica la regla de negocio.

Se agregó la relación inversa `Especie.vacunas` usando la tabla `vacuna_especie`
existente. Permite recorrer el catálogo desde el dominio sin escribir SQL allí.
Los métodos públicos originales del modelo conservan sus firmas.

### Pruebas por tanda

1. E13 comenzó con dos pruebas fallidas por ruta inexistente. Luego pasaron las
   32 pruebas del módulo de mascotas. Se agregó además el caso con consultas
   de dos mascotas para verificar el contenido y la separación por historia.
2. Catálogo: cuatro pruebas fallidas inicialmente y cuatro aprobadas tras implementar.
3. Vacunaciones: cuatro pruebas nuevas fallidas inicialmente, incluyendo el
   método de dominio aún pendiente. Después pasaron ocho pruebas acumuladas.
4. Pendientes: tres pruebas nuevas fallidas inicialmente. Después pasaron las
   once pruebas de catálogo y vacunación, incluyendo las reglas del modelo.

Se verificó el arranque real con Uvicorn, las respuestas 200 de `/api/health` y
`/docs`, y las seis operaciones en OpenAPI, usando una base temporal en memoria.
La suite completa finalizó con 212 pruebas aprobadas en 78,24 segundos y una
advertencia de deprecación de Starlette sobre httpx, ya presente antes de estos cambios.

### Recorrido manual en Swagger

1. Crear un cliente y una mascota; consultar E12 para obtener el id de historia.
2. Crear una vacuna con la especie de esa mascota y `obligatoria` en true.
3. Consultar las vacunas pendientes de la historia; debe aparecer esa vacuna.
4. Registrar su aplicación con `vacuna_id` y una fecha, por ejemplo `2026-01-01`.
5. Consultar vacunaciones para ver el registro y pendientes para comprobar que
   la vacuna aplicada dejó de aparecer.

## E19 — Carnet PDF

Se aprobó generar PDF e incorporar ReportLab. Se fijó `reportlab==5.1.0` y
sus dependencias instaladas Pillow y charset-normalizer en requirements.txt.
Para instalar en otra máquina, ejecutar desde backend
`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

`GET /api/mascotas/{mascota_id}/carnet-vacunas` descarga un PDF con nombre
`carnet-vacunas-{mascota_id}.pdf`. Incluye número de historia, nombre, especie
y nacimiento de la mascota, nombre y teléfono del responsable, vacunas aplicadas
y fechas en orden cronológico. Una historia vacía muestra “Sin vacunas registradas.”

El router devuelve bytes con `application/pdf` y encabezado de descarga.
El servicio reutiliza la búsqueda de mascotas activas. El método del modelo
`imprimir_carnet_vacunas()` ahora devuelve bytes y delega el diseño en
`reportes/carnet_vacunas.py`. Este generador de presentación es independiente
de los reportes estadísticos E61–E65 y su patrón Template Method.

El documento se construye en memoria. Los valores de texto se escapan antes de
pasarlos a los párrafos de ReportLab. La tabla ajusta nombres largos, continúa
en páginas sucesivas y repite el encabezado.

Las tres pruebas HTTP fallaron inicialmente por ruta inexistente. Después
pasaron la descarga, mascota inexistente y mascota inactiva. La suite completa
finalizó con 215 pruebas aprobadas en 61,82 segundos y la advertencia previa de
Starlette. Se verificaron Uvicorn, Swagger y el tipo PDF documentado en OpenAPI.

Se extrajo el contenido de ejemplos vacío, normal y extenso. El ejemplo de
90 filas adicionales produjo seis páginas y conservó todas las aplicaciones,
los acentos y los encabezados. Se revisaron visualmente el ejemplo normal y
una página de continuación con nombres largos.

Para probar, abrir `/docs`, elegir E19 y proporcionar el id de una mascota
activa. La respuesta permite descargar el carnet. Con esto están implementados
los ocho endpoints del bloque B, E12–E19.
