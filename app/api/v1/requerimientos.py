from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models import (
    Requerimiento,
    ReqItem,
    Articulo,
    Departamento,
    Clasificador,
    UnidadNegocio,
)
from app.schemas.requerimientos import ReqCreate, ReqOut, ReqDetail, ReqItemOut
from app.core.security import get_current_user

router = APIRouter(prefix="/api", tags=["Requerimientos"])


# ---------------------------------------------------------
# 📦 CREAR REQUERIMIENTO
# ---------------------------------------------------------
@router.post("/requerimientos", response_model=ReqOut)
def crear_requerimiento(payload: ReqCreate, db: Session = Depends(get_db)):
    if not db.get(Departamento, payload.departamento_id):
        raise HTTPException(400, "Departamento no existe")
    if not db.get(Clasificador, payload.clasificador_id):
        raise HTTPException(400, "Clasificador no existe")
    if not db.get(UnidadNegocio, payload.unidad_negocio_id):
        raise HTTPException(400, "Unidad de negocio no existe")

    articulo_map = {
        a.id: a.clasificador_id for a in db.query(Articulo.id, Articulo.clasificador_id).all()
    }
    for it in payload.items:
        if it.articulo_id not in articulo_map:
            raise HTTPException(400, f"Artículo {it.articulo_id} no existe")
        if articulo_map[it.articulo_id] != payload.clasificador_id:
            raise HTTPException(
                400, f"El artículo {it.articulo_id} no pertenece al clasificador seleccionado"
            )

    req = Requerimiento(
        departamento_id=payload.departamento_id,
        clasificador_id=payload.clasificador_id,
        unidad_negocio_id=payload.unidad_negocio_id,
        estatus="BORRADOR",
        fecha=datetime.utcnow(),
    )
    db.add(req)
    db.flush()

    for it in payload.items:
        db.add(ReqItem(requerimiento_id=req.id, articulo_id=it.articulo_id, cantidad=it.cantidad))

    db.commit()
    db.refresh(req)

    dep = db.get(Departamento, req.departamento_id)
    clas = db.get(Clasificador, req.clasificador_id)
    uen = db.get(UnidadNegocio, req.unidad_negocio_id)

    return {
        "id": req.id,
        "estatus": req.estatus,
        "fecha": req.fecha,
        "departamento_id": req.departamento_id,
        "clasificador_id": req.clasificador_id,
        "unidad_negocio_id": req.unidad_negocio_id,
        "departamento_nombre": dep.nombre if dep else None,
        "clasificador_nombre": clas.nombre if clas else None,
        "unidad_negocio_nombre": uen.nombre if uen else None,
    }


# ---------------------------------------------------------
# 📋 LISTAR REQUERIMIENTOS
# ---------------------------------------------------------
@router.get("/requerimientos", response_model=list[ReqOut])
def listar_requerimientos(db: Session = Depends(get_db)):
    query = (
        db.query(
            Requerimiento.id,
            Requerimiento.estatus,
            Requerimiento.fecha,
            Requerimiento.departamento_id,
            Departamento.nombre.label("departamento_nombre"),
            Requerimiento.clasificador_id,
            Clasificador.nombre.label("clasificador_nombre"),
            Requerimiento.unidad_negocio_id,
            UnidadNegocio.nombre.label("unidad_negocio_nombre"),
        )
        .join(Departamento, Departamento.id == Requerimiento.departamento_id)
        .join(Clasificador, Clasificador.id == Requerimiento.clasificador_id)
        .join(UnidadNegocio, UnidadNegocio.id == Requerimiento.unidad_negocio_id)
        .order_by(Requerimiento.id.desc())
    )

    return query.all()


# ---------------------------------------------------------
# 📄 OBTENER REQUERIMIENTO POR ID
# ---------------------------------------------------------
@router.get("/requerimientos/{req_id}", response_model=ReqOut)
def obtener_requerimiento(req_id: int, db: Session = Depends(get_db)):
    req = (
        db.query(
            Requerimiento.id,
            Requerimiento.estatus,
            Requerimiento.fecha,
            Requerimiento.departamento_id,
            Departamento.nombre.label("departamento_nombre"),
            Requerimiento.clasificador_id,
            Clasificador.nombre.label("clasificador_nombre"),
            Requerimiento.unidad_negocio_id,
            UnidadNegocio.nombre.label("unidad_negocio_nombre"),
        )
        .join(Departamento, Departamento.id == Requerimiento.departamento_id)
        .join(Clasificador, Clasificador.id == Requerimiento.clasificador_id)
        .join(UnidadNegocio, UnidadNegocio.id == Requerimiento.unidad_negocio_id)
        .filter(Requerimiento.id == req_id)
        .first()
    )

    if not req:
        raise HTTPException(404, "Requerimiento no encontrado")

    return req


# ---------------------------------------------------------
# 📦 DETALLE DE REQUERIMIENTO (con ítems)
# ---------------------------------------------------------
@router.get("/requerimientos/{req_id}/detalle", response_model=ReqDetail)
def obtener_requerimiento_detalle(req_id: int, db: Session = Depends(get_db)):
    req = (
        db.query(
            Requerimiento.id,
            Requerimiento.estatus,
            Requerimiento.fecha,
            Requerimiento.departamento_id,
            Departamento.nombre.label("departamento_nombre"),
            Requerimiento.clasificador_id,
            Clasificador.nombre.label("clasificador_nombre"),
            Requerimiento.unidad_negocio_id,
            UnidadNegocio.nombre.label("unidad_negocio_nombre"),
        )
        .join(Departamento, Departamento.id == Requerimiento.departamento_id)
        .join(Clasificador, Clasificador.id == Requerimiento.clasificador_id)
        .join(UnidadNegocio, UnidadNegocio.id == Requerimiento.unidad_negocio_id)
        .filter(Requerimiento.id == req_id)
        .first()
    )

    if not req:
        raise HTTPException(404, "Requerimiento no encontrado")

    items = (
        db.query(
            ReqItem.articulo_id,
            ReqItem.cantidad,
            Articulo.nombre.label("articulo_nombre"),
        )
        .join(Articulo, Articulo.id == ReqItem.articulo_id)
        .filter(ReqItem.requerimiento_id == req_id)
        .all()
    )

    return {**req._asdict(), "items": items}


# ---------------------------------------------------------
# 🔄 FLUJO DE APROBACIÓN
# ---------------------------------------------------------


def _get_req_with_names(req_id: int, db: Session):
    """Consulta auxiliar que devuelve el requerimiento con nombres relacionados."""
    result = (
        db.query(
            Requerimiento.id,
            Requerimiento.estatus,
            Requerimiento.fecha,
            Requerimiento.departamento_id,
            Departamento.nombre.label("departamento_nombre"),
            Requerimiento.clasificador_id,
            Clasificador.nombre.label("clasificador_nombre"),
            Requerimiento.unidad_negocio_id,
            UnidadNegocio.nombre.label("unidad_negocio_nombre"),
        )
        .join(Departamento, Departamento.id == Requerimiento.departamento_id)
        .join(Clasificador, Clasificador.id == Requerimiento.clasificador_id)
        .join(UnidadNegocio, UnidadNegocio.id == Requerimiento.unidad_negocio_id)
        .filter(Requerimiento.id == req_id)
        .first()
    )
    return result


@router.put("/requerimientos/{req_id}/revisar", response_model=ReqOut)
def enviar_a_revision(req_id: int, db: Session = Depends(get_db)):
    req = db.get(Requerimiento, req_id)
    if not req:
        raise HTTPException(404, "Requerimiento no encontrado")
    if req.estatus != "BORRADOR":
        raise HTTPException(400, "Solo se pueden enviar a revisión los borradores")

    req.estatus = "EN_REVISION"
    db.commit()
    db.refresh(req)

    return _get_req_with_names(req_id, db)


@router.put("/requerimientos/{req_id}/aprobar", response_model=ReqOut)
def aprobar_requerimiento(req_id: int, db: Session = Depends(get_db)):
    req = db.get(Requerimiento, req_id)
    if not req:
        raise HTTPException(404, "Requerimiento no encontrado")
    if req.estatus not in ("EN_REVISION",):
        raise HTTPException(400, "Solo se pueden aprobar los que están en revisión")

    req.estatus = "APROBADO"
    db.commit()
    db.refresh(req)

    return _get_req_with_names(req_id, db)


@router.put("/requerimientos/{req_id}/rechazar", response_model=ReqOut)
def rechazar_requerimiento(req_id: int, db: Session = Depends(get_db)):
    req = db.get(Requerimiento, req_id)
    if not req:
        raise HTTPException(404, "Requerimiento no encontrado")
    if req.estatus not in ("EN_REVISION",):
        raise HTTPException(400, "Solo se pueden rechazar los que están en revisión")

    req.estatus = "RECHAZADO"
    db.commit()
    db.refresh(req)

    return _get_req_with_names(req_id, db)

@router.get("/protegido")
def ruta_protegida(current_user: dict = Depends(get_current_user)):
    return {"mensaje": "Acceso concedido", "usuario": current_user}
