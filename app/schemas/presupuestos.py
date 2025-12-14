from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ---- CREATE ----
class PresupuestoCreate(BaseModel):
    departamento_id: int = Field(..., description="ID del departamento")
    clasificador_id: int = Field(..., description="ID del clasificador")
    unidad_negocio_id: int = Field(..., description="ID de la unidad de negocio")
    monto: float = Field(..., gt=0, description="Monto del presupuesto")
    periodo: str = Field(..., description="Período del presupuesto (Ej: '2025-Q1', '2025-01', '2025')")
    descripcion: Optional[str] = Field(None, description="Descripción opcional del presupuesto")


# ---- OUTPUT ----
class PresupuestoOut(BaseModel):
    id: int
    departamento_id: int
    clasificador_id: int
    unidad_negocio_id: int
    monto: float
    periodo: str
    descripcion: Optional[str]
    fecha_creacion: datetime

    # Nombres relacionados (opcionales para queries con joins)
    departamento_nombre: Optional[str] = None
    clasificador_nombre: Optional[str] = None
    unidad_negocio_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# ---- UPDATE ----
class PresupuestoUpdate(BaseModel):
    monto: Optional[float] = Field(None, gt=0, description="Nuevo monto del presupuesto")
    descripcion: Optional[str] = Field(None, description="Nueva descripción")
