# app/schemas/requerimientos.py
from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel, Field


# ------- Entrada -------
class ReqItemIn(BaseModel):
    articulo_id: int
    cantidad: int


class ReqCreate(BaseModel):
    departamento_id: int
    clasificador_id: int          # 🔹 nuevo campo (catálogo de clasificadores)
    unidad_negocio_id: int        # 🔹 nuevo campo (catálogo de unidades de negocio)
    items: list[ReqItemIn] = Field(default_factory=list)


# ------- Salida (listado / base) -------
class ReqOut(BaseModel):
    id: int
    estatus: str
    fecha: date | datetime
    departamento_id: int
    clasificador_id: int          # 🔹 incluir para referencia
    unidad_negocio_id: int        # 🔹 incluir para referencia

    # Estos campos vienen del JOIN (alias) en el endpoint de listado
    departamento_nombre: str | None = None
    clasificador_nombre: str | None = None
    unidad_negocio_nombre: str | None = None

    class Config:
        orm_mode = True


# ------- Detalle -------
class ReqItemOut(BaseModel):
    articulo_id: int
    cantidad: int
    articulo_nombre: str | None = None

    class Config:
        orm_mode = True


class ReqDetail(ReqOut):
    items: list[ReqItemOut] = []
