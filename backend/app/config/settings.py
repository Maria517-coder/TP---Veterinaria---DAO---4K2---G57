"""Configuración de la aplicación (variables de entorno con valores por defecto)."""
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    nombre_app: str = "TP Veterinaria - Red de Clínicas y Derivación de Laboratorio"
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./veterinaria.sqlite")
    )
    cors_origenes: list[str] = field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGENES", "http://localhost:5173,http://localhost:3000"
        ).split(",")
    )


settings = Settings()
