from collections import defaultdict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.db.models import (
    OrdenCompra,
    OCItem,
    Cotizacion,
    CotizacionProveedor,
    CotItem,
    Requerimiento,
    ReqItem,
)
from app.schemas.ocs import OCOut, OCDetail, GenerarOCsResponse, SeleccionLinea

router = APIRouter(prefix="/api", tags=["Órdenes de Compra"])


# ---------------------------------------------------------
# 📋 LISTAR ÓRDENES DE COMPRA
# ---------------------------------------------------------
@router.get("/ocs", response_model=list[OCOut])
def listar_ocs(db: Session = Depends(get_db)):
    """
    Devuelve el listado de Órdenes de Compra ordenadas por ID descendente.
    """
    return db.query(OrdenCompra).order_by(OrdenCompra.id.desc()).all()


# ---------------------------------------------------------
# 📄 DETALLE DE ORDEN DE COMPRA
# ---------------------------------------------------------
@router.get("/ocs/{oc_id}", response_model=OCDetail)
def detalle_oc(oc_id: int, db: Session = Depends(get_db)):
    """
    Devuelve una Orden de Compra con sus ítems asociados.
    """
    oc = (
        db.query(OrdenCompra)
        .options(joinedload(OrdenCompra.items))
        .filter_by(id=oc_id)
        .first()
    )
    if not oc:
        raise HTTPException(404, "OC no encontrada")
    return oc


# ---------------------------------------------------------
# 🧾 GENERAR ÓRDENES DE COMPRA DESDE UNA COTIZACIÓN
# ---------------------------------------------------------
@router.post("/ocs/generar-ocs/{cot_id}", response_model=GenerarOCsResponse)
def generar_ocs_desde_cotizacion(
    cot_id: int,
    seleccion: list[SeleccionLinea],
    db: Session = Depends(get_db),
):
    """
    Genera una o varias Órdenes de Compra a partir de una cotización aprobada.
    Recibe una lista de líneas seleccionadas (artículo, proveedor) y agrupa por proveedor.
    """
    cot = db.get(Cotizacion, cot_id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    if cot.estatus != "APROBADA":
        raise HTTPException(400, "La cotización debe estar APROBADA para generar OCs")

    # Evitar generar dos veces
    if db.query(OrdenCompra).filter_by(cotizacion_id=cot.id).first():
        raise HTTPException(400, "Ya existen OCs para esta cotización")

    # Cantidades del requerimiento asociado
    req_qty = {
        ri.articulo_id: ri.cantidad
        for ri in db.query(ReqItem).filter_by(requerimiento_id=cot.requerimiento_id).all()
    }
    if not req_qty:
        raise HTTPException(400, "El requerimiento no tiene items")

    # Precios cotizados: (proveedor, articulo) → precio_unit
    precios = {}
    cps = db.query(CotizacionProveedor).filter_by(cotizacion_id=cot.id).all()
    for cp in cps:
        for ci in db.query(CotItem).filter_by(cotizacion_proveedor_id=cp.id).all():
            precios[(cp.proveedor_id, ci.articulo_id)] = ci.precio_unit

    # Agrupación por proveedor
    por_proveedor: dict[int, list[tuple[int, int, float]]] = defaultdict(list)
    for linea in seleccion:
        aid = linea.articulo_id
        pid = linea.proveedor_id
        if aid not in req_qty:
            raise HTTPException(400, f"Artículo {aid} no está en el requerimiento")
        key = (pid, aid)
        if key not in precios:
            raise HTTPException(400, f"El proveedor {pid} no cotizó el artículo {aid}")
        por_proveedor[pid].append((aid, req_qty[aid], precios[key]))

    # Crear OCs agrupadas por proveedor
    oc_ids: list[int] = []
    for pid, rows in por_proveedor.items():
        oc = OrdenCompra(
            proveedor_id=pid,
            requerimiento_id=cot.requerimiento_id,
            cotizacion_id=cot.id,
            estatus="BORRADOR",
            fecha=datetime.utcnow(),
        )
        db.add(oc)
        db.flush()  # obtiene ID de la OC

        for aid, qty, pu in rows:
            db.add(
                OCItem(
                    orden_compra_id=oc.id,
                    articulo_id=aid,
                    cantidad=qty,
                    precio_unit=pu,
                )
            )

        db.commit()
        db.refresh(oc)
        oc_ids.append(oc.id)

    return {"oc_ids": oc_ids}

# ----------------------------
# FLUJO DE ESTATUS
# ----------------------------

@router.put("/{oc_id}/revisar", response_model=OCOut)
def enviar_a_revision(oc_id: int, db: Session = Depends(get_db)):
    oc = db.get(OrdenCompra, oc_id)
    if not oc:
        raise HTTPException(404, "OC no encontrada")
    if oc.estatus != "BORRADOR":
        raise HTTPException(400, "Solo se pueden enviar a revisión los borradores")
    oc.estatus = "EN_REVISION"
    db.commit()
    db.refresh(oc)
    return oc

@router.put("/{oc_id}/aprobar", response_model=OCOut)
def aprobar_oc(oc_id: int, db: Session = Depends(get_db)):
    oc = db.get(OrdenCompra, oc_id)
    if not oc:
        raise HTTPException(404, "OC no encontrada")
    if oc.estatus != "EN_REVISION":
        raise HTTPException(400, "Solo se pueden aprobar las OCs en revisión")
    oc.estatus = "APROBADA"
    db.commit()
    db.refresh(oc)
    return oc

@router.put("/{oc_id}/rechazar", response_model=OCOut)
def rechazar_oc(oc_id: int, db: Session = Depends(get_db)):
    oc = db.get(OrdenCompra, oc_id)
    if not oc:
        raise HTTPException(404, "OC no encontrada")
    if oc.estatus != "EN_REVISION":
        raise HTTPException(400, "Solo se pueden rechazar las OCs en revisión")
    oc.estatus = "RECHAZADA"
    db.commit()
    db.refresh(oc)
    return oc