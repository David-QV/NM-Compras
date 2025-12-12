import os
from dotenv import load_dotenv

# Cargar variables desde el archivo .env si existe
load_dotenv()

class Settings:
    # URL de la base de datos (usa SQLite por defecto si no hay .env ni variable)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./compras.db")

    # Otras configuraciones
    APP_NAME: str = os.getenv("APP_NAME", "Compras API")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# Instancia única de configuración
settings = Settings()

