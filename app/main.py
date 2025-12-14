from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import init_db
from app.api.v1.catalogos import router as catalogos_router
from app.api.v1.requerimientos import router as reqs_router
from app.api.v1.cotizaciones import router as cot_router
from app.api.v1.ocs import router as oc_router
from app.api.v1.auth import router as auth_router
from sqlalchemy import text
from app.db.session import SessionLocal
from app.api.v1.permisos import router as permisos_router
from app.api.v1.presupuestos import router as presupuestos_router
from app.api.v1.pagos import router as pagos_router

app = FastAPI(title="Compras API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health_check():
    db = SessionLocal()
    try:
        # Probar conexión a MySQL
        version = db.execute(text("SELECT VERSION();")).fetchone()
        db_status = "connected"
        mysql_version = version[0]
    except Exception as e:
        db_status = f"error: {str(e)}"
        mysql_version = None
    finally:
        db.close()

    return {
        "status": "ok",
        "database": db_status,
        "mysql_version": mysql_version
    }

app.include_router(auth_router)
app.include_router(catalogos_router)
app.include_router(reqs_router)
app.include_router(cot_router)
app.include_router(oc_router)
app.include_router(permisos_router)
app.include_router(presupuestos_router)
app.include_router(pagos_router)





