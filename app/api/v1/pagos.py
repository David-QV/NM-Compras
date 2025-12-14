from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from app.db.session import get_db
from app.db.models import ProgramacionPago, DetallePago, OrdenCompra, UnidadNegocio
from app.schemas.pagos import (
    ProgramacionPagoCreate,
    ProgramacionPagoOut,
    ProgramacionPagoDetalle,
    DetallePagoOut,
    MarcarPagadoIn
)

router = APIRouter(prefix="/api/pagos", tags=["Pagos"])


# ---------------------------------------------------------
# 📋 CREAR PROGRAMACIÓN DE PAGO
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=ProgramacionPagoDetalle,
    status_code=201,
    summary="Crear programación de pago",
    description="Crea una programación de pago para una OC aprobada con sus fechas y montos."
)
def crear_programacion_pago(payload: ProgramacionPagoCreate, db: Session = Depends(get_db)):
    """
    Crea una programación de pago para una Orden de Compra aprobada.

    - **orden_compra_id**: ID de la orden de compra (debe estar APROBADA)
    - **detalles**: Lista de pagos programados (fecha y monto)
    """
    # Validar que la OC exista y esté aprobada
    oc = db.get(OrdenCompra, payload.orden_compra_id)
    if not oc:
        raise HTTPException(404, "Orden de compra no encontrada")
    if oc.estatus != "APROBADA":
        raise HTTPException(400, "La orden de compra debe estar APROBADA para programar pagos")

    # Validar que no exista ya una programación de pago para esta OC
    existente = db.query(ProgramacionPago).filter_by(orden_compra_id=oc.id).first()
    if existente:
        raise HTTPException(400, "Ya existe una programación de pago para esta orden de compra")

    # Crear la programación de pago
    programacion = ProgramacionPago(
        orden_compra_id=payload.orden_compra_id,
        estatus="BORRADOR"
    )
    db.add(programacion)
    db.flush()

    # Crear los detalles de pago
    for detalle_in in payload.detalles:
        # Validar que la unidad de negocio exista
        if not db.get(UnidadNegocio, detalle_in.unidad_negocio_id):
            raise HTTPException(400, f"Unidad de negocio {detalle_in.unidad_negocio_id} no existe")

        detalle = DetallePago(
            programacion_pago_id=programacion.id,
            unidad_negocio_id=detalle_in.unidad_negocio_id,
            fecha_pago=detalle_in.fecha_pago,
            monto=detalle_in.monto,
            estatus="PENDIENTE"
        )
        db.add(detalle)

    db.commit()
    db.refresh(programacion)

    # Cargar los detalles para la respuesta
    programacion_completa = (
        db.query(ProgramacionPago)
        .options(joinedload(ProgramacionPago.detalles))
        .filter_by(id=programacion.id)
        .first()
    )

    return programacion_completa


# ---------------------------------------------------------
# 📋 LISTAR PROGRAMACIONES DE PAGO
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=list[ProgramacionPagoOut],
    summary="Listar programaciones de pago",
    description="Lista todas las programaciones de pago."
)
def listar_programaciones(db: Session = Depends(get_db)):
    """Lista todas las programaciones de pago ordenadas por fecha de creación descendente."""
    return db.query(ProgramacionPago).order_by(ProgramacionPago.fecha_creacion.desc()).all()


# ---------------------------------------------------------
# 📄 OBTENER PROGRAMACIÓN DE PAGO POR ID
# ---------------------------------------------------------
@router.get(
    "/{prog_id}",
    response_model=ProgramacionPagoDetalle,
    summary="Obtener programación de pago",
    description="Obtiene una programación de pago con todos sus detalles."
)
def obtener_programacion(prog_id: int, db: Session = Depends(get_db)):
    """Obtiene una programación de pago específica con sus detalles."""
    prog = (
        db.query(ProgramacionPago)
        .options(joinedload(ProgramacionPago.detalles))
        .filter_by(id=prog_id)
        .first()
    )
    if not prog:
        raise HTTPException(404, "Programación de pago no encontrada")
    return prog


# ---------------------------------------------------------
# ✅ PRIMERA APROBACIÓN
# ---------------------------------------------------------
@router.put(
    "/{prog_id}/primera-aprobacion",
    response_model=ProgramacionPagoOut,
    summary="Primera aprobación",
    description="Realiza la primera aprobación de la programación de pago."
)
def primera_aprobacion(
    prog_id: int,
    aprobador_id: int,
    db: Session = Depends(get_db)
):
    """
    Primera aprobación de la programación de pago.
    Cambia el estado de BORRADOR a PRIMERA_APROBACION.
    """
    prog = db.get(ProgramacionPago, prog_id)
    if not prog:
        raise HTTPException(404, "Programación de pago no encontrada")
    if prog.estatus != "BORRADOR":
        raise HTTPException(400, "Solo se puede aprobar programaciones en estado BORRADOR")

    prog.estatus = "PRIMERA_APROBACION"
    prog.aprobador_1 = aprobador_id
    prog.fecha_aprobacion_1 = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prog)
    return prog


# ---------------------------------------------------------
# ✅ SEGUNDA APROBACIÓN
# ---------------------------------------------------------
@router.put(
    "/{prog_id}/segunda-aprobacion",
    response_model=ProgramacionPagoOut,
    summary="Segunda aprobación",
    description="Realiza la segunda aprobación de la programación de pago."
)
def segunda_aprobacion(
    prog_id: int,
    aprobador_id: int,
    db: Session = Depends(get_db)
):
    """
    Segunda aprobación de la programación de pago.
    Cambia el estado de PRIMERA_APROBACION a APROBADA.
    """
    prog = db.get(ProgramacionPago, prog_id)
    if not prog:
        raise HTTPException(404, "Programación de pago no encontrada")
    if prog.estatus != "PRIMERA_APROBACION":
        raise HTTPException(400, "Solo se puede realizar la segunda aprobación después de la primera")

    prog.estatus = "APROBADA"
    prog.aprobador_2 = aprobador_id
    prog.fecha_aprobacion_2 = datetime.now(timezone.utc)

    db.commit()
    db.refresh(prog)
    return prog


# ---------------------------------------------------------
# 💰 MARCAR PAGO COMO PAGADO
# ---------------------------------------------------------
@router.put(
    "/detalle/{detalle_id}/marcar-pagado",
    response_model=DetallePagoOut,
    summary="Marcar pago como pagado",
    description="Marca un detalle de pago como PAGADO. Solo se puede hacer si la programación está APROBADA."
)
def marcar_pago_como_pagado(
    detalle_id: int,
    payload: MarcarPagadoIn,
    db: Session = Depends(get_db)
):
    """
    Marca un detalle de pago como PAGADO.

    - Solo se puede marcar como pagado si la programación está APROBADA
    - Registra la fecha de pago realizado
    - Permite agregar referencia y observaciones
    """
    detalle = db.get(DetallePago, detalle_id)
    if not detalle:
        raise HTTPException(404, "Detalle de pago no encontrado")

    # Verificar que la programación esté aprobada
    prog = db.get(ProgramacionPago, detalle.programacion_pago_id)
    if prog.estatus != "APROBADA":
        raise HTTPException(400, "Solo se pueden marcar pagos de programaciones APROBADAS")

    # Verificar que no esté ya pagado
    if detalle.estatus == "PAGADO":
        raise HTTPException(400, "Este pago ya está marcado como PAGADO")

    # Marcar como pagado
    detalle.estatus = "PAGADO"
    detalle.fecha_pago_realizado = datetime.now(timezone.utc)
    detalle.referencia = payload.referencia
    detalle.observaciones = payload.observaciones

    db.commit()
    db.refresh(detalle)
    return detalle


# ---------------------------------------------------------
# 📊 OBTENER PROGRAMACIÓN POR ORDEN DE COMPRA
# ---------------------------------------------------------
@router.get(
    "/orden-compra/{oc_id}",
    response_model=ProgramacionPagoDetalle,
    summary="Obtener programación por OC",
    description="Obtiene la programación de pago asociada a una orden de compra."
)
def obtener_por_orden_compra(oc_id: int, db: Session = Depends(get_db)):
    """Obtiene la programación de pago de una orden de compra específica."""
    prog = (
        db.query(ProgramacionPago)
        .options(joinedload(ProgramacionPago.detalles))
        .filter_by(orden_compra_id=oc_id)
        .first()
    )
    if not prog:
        raise HTTPException(404, "No hay programación de pago para esta orden de compra")
    return prog
