"""Usuario del sistema con rol y credenciales hasheadas."""
import enum

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config.database import Base


class RolUsuario(str, enum.Enum):
    """Roles mínimos del sistema."""

    ADMIN = "ADMIN"
    VETERINARIO = "VETERINARIO"


class Usuario(Base):
    """Usuario autenticable. La contraseña se guarda solo como hash con sal."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre_usuario: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
