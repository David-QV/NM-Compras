from pydantic import BaseModel
from typing import Optional

# ---- UNIDAD DE NEGOCIO ----
class UnidadNegocioBase(BaseModel):
    nombre: str

class UnidadNegocioCreate(UnidadNegocioBase):
    pass

class UnidadNegocioOut(UnidadNegocioBase):
    id: int
    class Config:
        from_attributes = True



# ---- CLASIFICADOR ----
class ClasificadorBase(BaseModel):
    nombre: str

class ClasificadorCreate(ClasificadorBase):
    pass

class ClasificadorOut(ClasificadorBase):
    id: int

    class Config:
        from_attributes = True


# ---- ARTÍCULO ----
class ArticuloCreate(BaseModel):
    nombre: str
    clasificador_id: Optional[int] = None  # ahora es ID (FK)

class ArticuloOut(BaseModel):
    id: int
    nombre: str
    clasificador_rel: Optional[ClasificadorOut] = None  # muestra el objeto clasificador

    class Config:
        from_attributes = True


# ---- DEPARTAMENTO ----
class DepartamentoCreate(BaseModel):
    nombre: str

class DepartamentoOut(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True
