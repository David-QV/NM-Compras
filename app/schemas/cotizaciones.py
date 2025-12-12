from pydantic import BaseModel, conint, condecimal
from typing import List

class CotCreate(BaseModel):
    requerimiento_id: int

class CotOut(BaseModel):
    id: int
    requerimiento_id: int
    estatus: str
    class Config:
        from_attributes = True

class CotProvAdd(BaseModel):
    proveedor_id: int

class CotProvOut(BaseModel):
    id: int
    proveedor_id: int
    class Config:
        from_attributes = True

class CotItemIn(BaseModel):
    articulo_id: int
    precio_unit: condecimal(ge=0)  # cantidad se toma del requerimiento

class CotComparativo(BaseModel):
    # Estructura simple para ver precios por proveedor
    items: List[dict]
    proveedores: List[dict]

class SeleccionLinea(BaseModel):
    proveedor_id: int
    articulo_id: int

class GenerarOCsResponse(BaseModel):
    oc_ids: List[int]
