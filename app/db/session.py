import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

# Leer URL desde variable de entorno (ya embebida en el contenedor)
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear motor dinámico
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    connect_args={"charset": "utf8mb4"} if DATABASE_URL.startswith("mysql") else {},
    echo=False
)

# Crear sesión
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Inicializar las tablas
def init_db():
    from app.db import models  # noqa
    Base.metadata.create_all(bind=engine)

# Dependencia para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
