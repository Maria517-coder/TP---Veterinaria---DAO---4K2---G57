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
