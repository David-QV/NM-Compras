from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict

from app.db.session import get_db
from app.db.models import (
    Requerimiento, ReqItem,
    Proveedor,
    Cotizacion, CotizacionProveedor, CotItem,
    OrdenCompra, OCItem
)
from app.schemas.cotizaciones import (
    CotCreate, CotOut, CotProvAdd, CotProvOut, CotItemIn,
    CotComparativo, SeleccionLinea, GenerarOCsResponse
)

router = APIRouter(prefix="/api", tags=["Cotizaciones"])

# -------- Crear/consultar cotización --------
@router.post("/cotizaciones", response_model=CotOut)
def crear_cotizacion(payload: CotCreate, db: Session = Depends(get_db)):
    req = db.get(Requerimiento, payload.requerimiento_id)
    if not req:
        raise HTTPException(404, "Requerimiento no existe")
    if req.estatus != "APROBADO":
        raise HTTPException(400, "El requerimiento debe estar APROBADO para cotizar")
    if db.query(Cotizacion).filter_by(requerimiento_id=req.id).first():
        # Para el MVP, evita duplicar cotización del mismo requerimiento
        raise HTTPException(400, "Ya existe una cotización para este requerimiento")
    cot = Cotizacion(requerimiento_id=req.id, estatus="ABIERTA")
    db.add(cot); db.commit(); db.refresh(cot)
    return cot

@router.get("/cotizaciones/{cot_id}", response_model=CotOut)
def obtener_cotizacion(cot_id: int, db: Session = Depends(get_db)):
    cot = db.get(Cotizacion, cot_id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    return cot

# -------- Proveedores en cotización --------
@router.post("/cotizaciones/{cot_id}/proveedores", response_model=CotProvOut)
def agregar_proveedor(cot_id: int, payload: CotProvAdd, db: Session = Depends(get_db)):
    cot = db.get(Cotizacion, cot_id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    if cot.estatus != "ABIERTA":
        raise HTTPException(400, "Cotización cerrada; no se pueden agregar proveedores")
    if not db.get(Proveedor, payload.proveedor_id):
        raise HTTPException(404, "Proveedor no existe")
    # evita duplicado
    ya = db.query(CotizacionProveedor).filter_by(cotizacion_id=cot.id, proveedor_id=payload.proveedor_id).first()
    if ya:
        return ya
    cp = CotizacionProveedor(cotizacion_id=cot.id, proveedor_id=payload.proveedor_id)
    db.add(cp); db.commit(); db.refresh(cp)
    return cp

# -------- Cargar precios por proveedor --------
@router.post("/cotizaciones/{cot_id}/proveedores/{prov_id}/items")
def cargar_items_proveedor(cot_id: int, prov_id: int, items: list[CotItemIn], db: Session = Depends(get_db)):
    cot = db.get(Cotizacion, cot_id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    if cot.estatus != "ABIERTA":
        raise HTTPException(400, "Cotización cerrada; no se pueden editar precios")
    cp = db.query(CotizacionProveedor).filter_by(cotizacion_id=cot.id, proveedor_id=prov_id).first()
    if not cp:
        raise HTTPException(404, "El proveedor no está agregado a esta cotización")

    # Cantidades vienen del requerimiento
    req_items = {ri.articulo_id: ri.cantidad for ri in db.query(ReqItem).filter_by(requerimiento_id=cot.requerimiento_id).all()}
    if not req_items:
        raise HTTPException(400, "El requerimiento no tiene items")

    # upsert simple
    existentes = {(ci.articulo_id): ci for ci in db.query(CotItem).filter_by(cotizacion_proveedor_id=cp.id).all()}
    for it in items:
        if it.articulo_id not in req_items:
            raise HTTPException(400, f"Artículo {it.articulo_id} no está en el requerimiento")
        if it.articulo_id in existentes:
            existentes[it.articulo_id].precio_unit = float(it.precio_unit)
            existentes[it.articulo_id].cantidad = req_items[it.articulo_id]
        else:
            db.add(CotItem(
                cotizacion_proveedor_id=cp.id,
                articulo_id=it.articulo_id,
                cantidad=req_items[it.articulo_id],
                precio_unit=float(it.precio_unit),
            ))
    db.commit()
    return {"ok": True}

# -------- Comparativo --------
@router.get("/cotizaciones/{cot_id}/comparativo", response_model=CotComparativo)
def comparativo(cot_id: int, db: Session = Depends(get_db)):
    cot = db.query(Cotizacion).options(
        joinedload(Cotizacion.proveedores).joinedload(CotizacionProveedor.items)
    ).filter_by(id=cot_id).first()
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")

    # items del requerimiento (para ordenar/mostrar cantidades)
    req_items = {ri.articulo_id: ri.cantidad for ri in db.query(ReqItem).filter_by(requerimiento_id=cot.requerimiento_id).all()}
    items_list = [{"articulo_id": aid, "cantidad": qty} for aid, qty in req_items.items()]

    proveedores = []
    for cp in cot.proveedores:
        precios = [{"articulo_id": ci.articulo_id, "precio_unit": ci.precio_unit} for ci in cp.items]
        proveedores.append({"proveedor_id": cp.proveedor_id, "precios": precios})
    return {"items": items_list, "proveedores": proveedores}

# ---------------------------------------------------------
# 🔄 APROBAR COTIZACIÓN
# ---------------------------------------------------------
@router.put("/cotizaciones/{cot_id}/aprobar", response_model=CotOut)
def aprobar_cotizacion(cot_id: int, db: Session = Depends(get_db)):
    """
    Cambia el estatus de una cotización de ABIERTA a APROBADA.
    """
    cot = db.get(Cotizacion, cot_id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    if cot.estatus != "ABIERTA":
        raise HTTPException(400, "Solo se pueden aprobar cotizaciones abiertas")

    cot.estatus = "APROBADA"
    db.commit()
    db.refresh(cot)
    return cot


# ---------------------------------------------------------
# ❌ RECHAZAR COTIZACIÓN
# ---------------------------------------------------------
@router.put("/cotizaciones/{cot_id}/rechazar", response_model=CotOut)
def rechazar_cotizacion(cot_id: int, db: Session = Depends(get_db)):
    """
    Cambia el estatus de una cotización de ABIERTA a RECHAZADA.
    """
    cot = db.get(Cotizacion, cot_id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    if cot.estatus != "ABIERTA":
        raise HTTPException(400, "Solo se pueden rechazar cotizaciones abiertas")

    cot.estatus = "RECHAZADA"
    db.commit()
    db.refresh(cot)
    return cot
