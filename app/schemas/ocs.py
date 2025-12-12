from pydantic import BaseModel
from typing import List


# ---------------------------------------------------------
# 🧾 SCHEMAS PARA ÓRDENES DE COMPRA
# ---------------------------------------------------------

class OCItemOut(BaseModel):
    articulo_id: int
    cantidad: int
    precio_unit: float

    class Config:
        from_attributes = True


class OCOut(BaseModel):
    id: int
    proveedor_id: int
    requerimiento_id: int
    cotizacion_id: int
    estatus: str

    class Config:
        from_attributes = True


class OCDetail(OCOut):
    items: List[OCItemOut]


# ---------------------------------------------------------
# ⚙️ SCHEMAS PARA GENERAR OCs DESDE COTIZACIÓN
# ---------------------------------------------------------

class SeleccionLinea(BaseModel):
    articulo_id: int
    proveedor_id: int


class GenerarOCsResponse(BaseModel):
    oc_ids: List[int]
