from fastapi import APIRouter
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login")
def login():
    """Devuelve un JWT de prueba (sin validar usuario todavía)."""
    # Simula un usuario fijo
    fake_user = {"sub": "usuario_demo", "rol": "tester"}
    token = create_access_token(fake_user)
    return {"access_token": token, "token_type": "bearer"}
