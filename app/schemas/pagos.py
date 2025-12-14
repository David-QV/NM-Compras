from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ---- DETALLE DE PAGO ----
class DetallePagoIn(BaseModel):
    """Esquema para crear un detalle de pago"""
    unidad_negocio_id: int = Field(..., description="ID de la unidad de negocio")
    fecha_pago: datetime = Field(..., description="Fecha programada de pago")
    monto: float = Field(..., gt=0, description="Monto a pagar (debe ser mayor a 0)")


class DetallePagoOut(BaseModel):
    """Esquema de salida para detalle de pago"""
    id: int
    programacion_pago_id: int
    unidad_negocio_id: int
    fecha_pago: datetime
    monto: float
    estatus: str
    fecha_pago_realizado: Optional[datetime]
    referencia: Optional[str]
    observaciones: Optional[str]

    class Config:
        from_attributes = True


# ---- PROGRAMACIÓN DE PAGO ----
class ProgramacionPagoCreate(BaseModel):
    """Esquema para crear una programación de pago"""
    orden_compra_id: int = Field(..., description="ID de la orden de compra")
    detalles: List[DetallePagoIn] = Field(..., min_length=1, description="Lista de pagos a programar")


class ProgramacionPagoOut(BaseModel):
    """Esquema de salida para programación de pago"""
    id: int
    orden_compra_id: int
    estatus: str
    fecha_creacion: datetime
    aprobador_1: Optional[int]
    fecha_aprobacion_1: Optional[datetime]
    aprobador_2: Optional[int]
    fecha_aprobacion_2: Optional[datetime]

    class Config:
        from_attributes = True


class ProgramacionPagoDetalle(ProgramacionPagoOut):
    """Esquema de salida con detalles de pagos incluidos"""
    detalles: List[DetallePagoOut]

    class Config:
        from_attributes = True


# ---- MARCAR PAGO COMO PAGADO ----
class MarcarPagadoIn(BaseModel):
    """Esquema para marcar un pago como pagado"""
    referencia: Optional[str] = Field(None, description="Número de referencia o comprobante")
    observaciones: Optional[str] = Field(None, description="Observaciones del pago")
