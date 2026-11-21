"""Endpoints E20 a E31 de punta a punta por HTTP."""
import pytest
from fastapi.testclient import TestClient


def _crear_clinica(client: TestClient, nombre: str = "Centro") -> dict[str, object]:
    """Da de alta una clínica por HTTP."""
    respuesta = client.post("/api/red/clinicas", json={"nombre": nombre})
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _crear_veterinario(
    client: TestClient,
    clinica_id: object,
    matricula: str = "MP-1",
    nombre: str = "Eva",
) -> dict[str, object]:
    """Da de alta un veterinario por HTTP."""
    respuesta = client.post(
        f"/api/clinicas/{clinica_id}/veterinarios",
        json={"matricula": matricula, "nombre": nombre},
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


# --- Red y clínicas (E20-E24) ---


def test_e20_obtener_red(client: TestClient) -> None:
    """GET /red devuelve solo id y nombre."""
    respuesta = client.get("/api/red")

    assert respuesta.status_code == 200
    assert set(respuesta.json()) == {"id", "nombre"}


def test_e21_agregar_clinica(client: TestClient) -> None:
    """POST /red/clinicas da de alta en la red y recorta el nombre."""
    respuesta = client.post("/api/red/clinicas", json={"nombre": "  Centro  "})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Centro"
    assert cuerpo["red_id"] > 0


def test_e21_clinica_duplicada_da_409(client: TestClient) -> None:
    """El nombre exacto no se puede repetir."""
    _crear_clinica(client)

    respuesta = client.post("/api/red/clinicas", json={"nombre": "Centro"})

    assert respuesta.status_code == 409
    assert "detalle" in respuesta.json()


def test_e21_nombre_invalido_da_422(client: TestClient) -> None:
    """Pydantic rechaza el nombre vacío."""
    respuesta = client.post("/api/red/clinicas", json={"nombre": "   "})

    assert respuesta.status_code == 422


def test_e22_listar_clinicas(client: TestClient) -> None:
    """GET /clinicas devuelve todas."""
    _crear_clinica(client, "Centro")
    _crear_clinica(client, "Sur")

    respuesta = client.get("/api/clinicas")

    assert respuesta.status_code == 200
    assert {clinica["nombre"] for clinica in respuesta.json()} == {"Centro", "Sur"}


def test_e23_obtener_clinica(client: TestClient) -> None:
    """GET /clinicas/{id} devuelve la clínica pedida."""
    creada = _crear_clinica(client)

    respuesta = client.get(f"/api/clinicas/{creada['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Centro"


def test_e23_inexistente_da_404(client: TestClient) -> None:
    respuesta = client.get("/api/clinicas/9999")

    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


def test_e24_actualizar_clinica(client: TestClient) -> None:
    """PUT /clinicas/{id} reemplaza el nombre."""
    creada = _crear_clinica(client)

    respuesta = client.put(
        f"/api/clinicas/{creada['id']}", json={"nombre": "Centro Norte"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Centro Norte"


def test_e24_duplicada_da_409(client: TestClient) -> None:
    centro = _crear_clinica(client, "Centro")
    _crear_clinica(client, "Sur")

    respuesta = client.put(f"/api/clinicas/{centro['id']}", json={"nombre": "Sur"})

    assert respuesta.status_code == 409


def test_e24_inexistente_da_404(client: TestClient) -> None:
    respuesta = client.put("/api/clinicas/9999", json={"nombre": "Centro"})

    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


# --- Veterinarios (E25-E28) ---


def test_e25_crear_veterinario(client: TestClient) -> None:
    """POST /clinicas/{id}/veterinarios da de alta un veterinario activo."""
    clinica = _crear_clinica(client)

    respuesta = client.post(
        f"/api/clinicas/{clinica['id']}/veterinarios",
        json={"matricula": "  MP-1  ", "nombre": "  Eva  "},
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["matricula"] == "MP-1"
    assert cuerpo["nombre"] == "Eva"
    assert cuerpo["activo"] is True


def test_e25_matricula_duplicada_da_409(client: TestClient) -> None:
    clinica = _crear_clinica(client)
    _crear_veterinario(client, clinica["id"], "MP-1")

    respuesta = client.post(
        f"/api/clinicas/{clinica['id']}/veterinarios",
        json={"matricula": "MP-1", "nombre": "Ana"},
    )

    assert respuesta.status_code == 409


def test_e25_matricula_de_inactivo_bloquea(client: TestClient) -> None:
    clinica = _crear_clinica(client)
    veterinario = _crear_veterinario(client, clinica["id"], "MP-1")
    assert client.delete(f"/api/veterinarios/{veterinario['id']}").status_code == 204

    respuesta = client.post(
        f"/api/clinicas/{clinica['id']}/veterinarios",
        json={"matricula": "MP-1", "nombre": "Ana"},
    )

    assert respuesta.status_code == 409


def test_e25_clinica_inexistente_da_404(client: TestClient) -> None:
    respuesta = client.post(
        "/api/clinicas/9999/veterinarios",
        json={"matricula": "MP-1", "nombre": "Eva"},
    )

    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


def test_e25_datos_invalidos_dan_422(client: TestClient) -> None:
    clinica = _crear_clinica(client)

    respuesta = client.post(
        f"/api/clinicas/{clinica['id']}/veterinarios",
        json={"matricula": "", "nombre": "Eva"},
    )

    assert respuesta.status_code == 422


def test_e26_listar_veterinarios(client: TestClient) -> None:
    """GET devuelve solo los activos de la clínica."""
    clinica = _crear_clinica(client)
    eva = _crear_veterinario(client, clinica["id"], "MP-1", "Eva")
    _crear_veterinario(client, clinica["id"], "MP-2", "Ana")
    assert client.delete(f"/api/veterinarios/{eva['id']}").status_code == 204

    respuesta = client.get(f"/api/clinicas/{clinica['id']}/veterinarios")

    assert respuesta.status_code == 200
    assert [vet["nombre"] for vet in respuesta.json()] == ["Ana"]


def test_e26_clinica_inexistente_da_404(client: TestClient) -> None:
    respuesta = client.get("/api/clinicas/9999/veterinarios")

    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


def test_e27_actualizar_veterinario(client: TestClient) -> None:
    clinica = _crear_clinica(client)
    veterinario = _crear_veterinario(client, clinica["id"])

    respuesta = client.put(
        f"/api/veterinarios/{veterinario['id']}",
        json={"matricula": "MP-9", "nombre": "Eva María"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["matricula"] == "MP-9"


def test_e27_mantiene_su_matricula(client: TestClient) -> None:
    clinica = _crear_clinica(client)
    veterinario = _crear_veterinario(client, clinica["id"], "MP-1")

    respuesta = client.put(
        f"/api/veterinarios/{veterinario['id']}",
        json={"matricula": "MP-1", "nombre": "Eva María"},
    )

    assert respuesta.status_code == 200


def test_e27_matricula_duplicada_da_409(client: TestClient) -> None:
    clinica = _crear_clinica(client)
    eva = _crear_veterinario(client, clinica["id"], "MP-1")
    _crear_veterinario(client, clinica["id"], "MP-2", "Ana")

    respuesta = client.put(
        f"/api/veterinarios/{eva['id']}",
        json={"matricula": "MP-2", "nombre": "Eva"},
    )

    assert respuesta.status_code == 409


def test_e27_inexistente_da_404(client: TestClient) -> None:
    respuesta = client.put(
        "/api/veterinarios/9999", json={"matricula": "MP-1", "nombre": "Eva"}
    )

    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


def test_e28_eliminar_veterinario(client: TestClient) -> None:
    clinica = _crear_clinica(client)
    veterinario = _crear_veterinario(client, clinica["id"])

    respuesta = client.delete(f"/api/veterinarios/{veterinario['id']}")

    assert respuesta.status_code == 204
    assert not respuesta.content
    assert client.put(
        f"/api/veterinarios/{veterinario['id']}",
        json={"matricula": "MP-1", "nombre": "Eva"},
    ).status_code == 404


def test_e28_inexistente_da_404(client: TestClient) -> None:
    respuesta = client.delete("/api/veterinarios/9999")

    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


# --- Tipos de muestra (E29-E31) ---


def test_e29_listar_tipos_muestra(client: TestClient) -> None:
    """Los tipos sembrados se listan con su costo como texto."""
    respuesta = client.get("/api/tipos-muestra")

    assert respuesta.status_code == 200
    tipos = respuesta.json()
    assert {tipo["nombre"] for tipo in tipos} >= {"SANGRE", "ORINA"}
    assert all(isinstance(tipo["costo_analisis"], str) for tipo in tipos)


def test_e30_crear_tipo_muestra(client: TestClient) -> None:
    respuesta = client.post(
        "/api/tipos-muestra", json={"nombre": "NUEVO", "costo_analisis": "99.50"}
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "NUEVO"
    assert cuerpo["costo_analisis"] == "99.50"


def test_e30_duplicado_da_409(client: TestClient) -> None:
    assert client.post(
        "/api/tipos-muestra", json={"nombre": "NUEVO", "costo_analisis": "1"}
    ).status_code == 201

    respuesta = client.post(
        "/api/tipos-muestra", json={"nombre": "NUEVO", "costo_analisis": "2"}
    )

    assert respuesta.status_code == 409


def test_e30_float_da_422(client: TestClient) -> None:
    respuesta = client.post(
        "/api/tipos-muestra", json={"nombre": "NUEVO", "costo_analisis": 12.5}
    )

    assert respuesta.status_code == 422


def test_e30_negativo_da_422(client: TestClient) -> None:
    respuesta = client.post(
        "/api/tipos-muestra", json={"nombre": "NUEVO", "costo_analisis": "-1"}
    )

    assert respuesta.status_code == 422


def test_e31_actualizar_tipo_muestra(client: TestClient) -> None:
    creado = client.post(
        "/api/tipos-muestra", json={"nombre": "NUEVO", "costo_analisis": "1"}
    ).json()

    respuesta = client.put(
        f"/api/tipos-muestra/{creado['id']}",
        json={"nombre": "NUEVO 2", "costo_analisis": "2.00"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "NUEVO 2"
    assert respuesta.json()["costo_analisis"] == "2.00"


def test_e31_mantiene_su_nombre(client: TestClient) -> None:
    creado = client.post(
        "/api/tipos-muestra", json={"nombre": "NUEVO", "costo_analisis": "1"}
    ).json()

    respuesta = client.put(
        f"/api/tipos-muestra/{creado['id']}",
        json={"nombre": "NUEVO", "costo_analisis": "3.00"},
    )

    assert respuesta.status_code == 200


def test_e31_duplicado_da_409(client: TestClient) -> None:
    sangre = client.get("/api/tipos-muestra").json()[0]
    creado = client.post(
        "/api/tipos-muestra", json={"nombre": "NUEVO", "costo_analisis": "1"}
    ).json()

    respuesta = client.put(
        f"/api/tipos-muestra/{creado['id']}",
        json={"nombre": sangre["nombre"], "costo_analisis": "2"},
    )

    assert respuesta.status_code == 409


def test_e31_inexistente_da_404(client: TestClient) -> None:
    respuesta = client.put(
        "/api/tipos-muestra/9999", json={"nombre": "NUEVO", "costo_analisis": "1"}
    )

    assert respuesta.status_code == 404
    assert "detalle" in respuesta.json()


# --- Contrato HTTP ---


def test_openapi_expone_los_12_endpoints(client: TestClient) -> None:
    """Los 12 IDs del Excel aparecen como operaciones bajo /api."""
    rutas = [
        "/api/red",
        "/api/red/clinicas",
        "/api/clinicas",
        "/api/clinicas/{id}",
        "/api/clinicas/{id}/veterinarios",
        "/api/veterinarios/{id}",
        "/api/tipos-muestra",
        "/api/tipos-muestra/{id}",
    ]
    esquema = client.get("/openapi.json").json()

    assert all(ruta in esquema["paths"] for ruta in rutas)
    total = sum(
        sum(
            1
            for metodo in esquema["paths"][ruta]
            if metodo in {"get", "post", "put", "delete"}
        )
        for ruta in rutas
    )
    assert total == 12
