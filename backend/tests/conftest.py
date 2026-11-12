"""Configuración de pytest: usa una base SQLite aparte para los tests."""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_veterinaria.sqlite"
