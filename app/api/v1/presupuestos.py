from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db.models import Presupuesto, Departamento, Clasificador, UnidadNegocio
from app.schemas.presupuestos import PresupuestoCreate, PresupuestoOut, PresupuestoUpdate

router = APIRouter(prefix="/api/presupuestos", tags=["Presupuestos"])


# ---------------------------------------------------------
# 📊 CREAR PRESUPUESTO
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=PresupuestoOut,
    status_code=201,
    summary="Crear nuevo presupuesto",
    description="Crea un presupuesto para una combinación de departamento, clasificador y unidad de negocio."
)
def crear_presupuesto(payload: PresupuestoCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo presupuesto.

    - **departamento_id**: ID del departamento
    - **clasificador_id**: ID del clasificador
    - **unidad_negocio_id**: ID de la unidad de negocio
    - **monto**: Monto del presupuesto (debe ser mayor a 0)
    - **periodo**: Período del presupuesto (Ej: "2025-Q1", "2025-01", "2025")
    - **descripcion**: Descripción opcional
    """
    # Validar que existan las entidades relacionadas
    if not db.get(Departamento, payload.departamento_id):
        raise HTTPException(400, "Departamento no existe")
    if not db.get(Clasificador, payload.clasificador_id):
        raise HTTPException(400, "Clasificador no existe")
    if not db.get(UnidadNegocio, payload.unidad_negocio_id):
        raise HTTPException(400, "Unidad de negocio no existe")

    # Validar que no exista un presupuesto duplicado para la misma combinación y período
    existente = db.query(Presupuesto).filter_by(
        departamento_id=payload.departamento_id,
        clasificador_id=payload.clasificador_id,
        unidad_negocio_id=payload.unidad_negocio_id,
        periodo=payload.periodo
    ).first()

    if existente:
        raise HTTPException(
            400,
            f"Ya existe un presupuesto para esta combinación en el período {payload.periodo}"
        )

    # Crear presupuesto
    presupuesto = Presupuesto(**payload.model_dump())
    db.add(presupuesto)
    db.commit()
    db.refresh(presupuesto)

    # Obtener nombres para la respuesta
    dep = db.get(Departamento, presupuesto.departamento_id)
    clas = db.get(Clasificador, presupuesto.clasificador_id)
    uen = db.get(UnidadNegocio, presupuesto.unidad_negocio_id)

    return PresupuestoOut(
        **presupuesto.__dict__,
        departamento_nombre=dep.nombre if dep else None,
        clasificador_nombre=clas.nombre if clas else None,
        unidad_negocio_nombre=uen.nombre if uen else None
    )


# ---------------------------------------------------------
# 📋 LISTAR PRESUPUESTOS
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=list[PresupuestoOut],
    summary="Listar presupuestos",
    description="Lista todos los presupuestos con filtros opcionales."
)
def listar_presupuestos(
    departamento_id: Optional[int] = Query(None, description="Filtrar por departamento"),
    clasificador_id: Optional[int] = Query(None, description="Filtrar por clasificador"),
    unidad_negocio_id: Optional[int] = Query(None, description="Filtrar por unidad de negocio"),
    periodo: Optional[str] = Query(None, description="Filtrar por período"),
    db: Session = Depends(get_db)
):
    """
    Lista todos los presupuestos con filtros opcionales.
    """
    query = (
        db.query(
            Presupuesto.id,
            Presupuesto.departamento_id,
            Presupuesto.clasificador_id,
            Presupuesto.unidad_negocio_id,
            Presupuesto.monto,
            Presupuesto.periodo,
            Presupuesto.descripcion,
            Presupuesto.fecha_creacion,
            Departamento.nombre.label("departamento_nombre"),
            Clasificador.nombre.label("clasificador_nombre"),
            UnidadNegocio.nombre.label("unidad_negocio_nombre"),
        )
        .join(Departamento, Departamento.id == Presupuesto.departamento_id)
        .join(Clasificador, Clasificador.id == Presupuesto.clasificador_id)
        .join(UnidadNegocio, UnidadNegocio.id == Presupuesto.unidad_negocio_id)
    )

    # Aplicar filtros opcionales
    if departamento_id:
        query = query.filter(Presupuesto.departamento_id == departamento_id)
    if clasificador_id:
        query = query.filter(Presupuesto.clasificador_id == clasificador_id)
    if unidad_negocio_id:
        query = query.filter(Presupuesto.unidad_negocio_id == unidad_negocio_id)
    if periodo:
        query = query.filter(Presupuesto.periodo == periodo)

    query = query.order_by(Presupuesto.fecha_creacion.desc())

    return query.all()


# ---------------------------------------------------------
# 📄 OBTENER PRESUPUESTO POR ID
# ---------------------------------------------------------
@router.get(
    "/{presupuesto_id}",
    response_model=PresupuestoOut,
    summary="Obtener presupuesto por ID",
    description="Obtiene un presupuesto específico por su ID."
)
def obtener_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un presupuesto específico por su ID.
    """
    result = (
        db.query(
            Presupuesto.id,
            Presupuesto.departamento_id,
            Presupuesto.clasificador_id,
            Presupuesto.unidad_negocio_id,
            Presupuesto.monto,
            Presupuesto.periodo,
            Presupuesto.descripcion,
            Presupuesto.fecha_creacion,
            Departamento.nombre.label("departamento_nombre"),
            Clasificador.nombre.label("clasificador_nombre"),
            UnidadNegocio.nombre.label("unidad_negocio_nombre"),
        )
        .join(Departamento, Departamento.id == Presupuesto.departamento_id)
        .join(Clasificador, Clasificador.id == Presupuesto.clasificador_id)
        .join(UnidadNegocio, UnidadNegocio.id == Presupuesto.unidad_negocio_id)
        .filter(Presupuesto.id == presupuesto_id)
        .first()
    )

    if not result:
        raise HTTPException(404, "Presupuesto no encontrado")

    return result


# ---------------------------------------------------------
# ✏️ ACTUALIZAR PRESUPUESTO
# ---------------------------------------------------------
@router.put(
    "/{presupuesto_id}",
    response_model=PresupuestoOut,
    summary="Actualizar presupuesto",
    description="Actualiza el monto y/o descripción de un presupuesto existente."
)
def actualizar_presupuesto(
    presupuesto_id: int,
    payload: PresupuestoUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza el monto y/o descripción de un presupuesto.
    No se pueden cambiar el departamento, clasificador, unidad de negocio o período.
    """
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        raise HTTPException(404, "Presupuesto no encontrado")

    # Actualizar solo los campos que se enviaron
    if payload.monto is not None:
        presupuesto.monto = payload.monto
    if payload.descripcion is not None:
        presupuesto.descripcion = payload.descripcion

    db.commit()
    db.refresh(presupuesto)

    # Obtener nombres para la respuesta
    dep = db.get(Departamento, presupuesto.departamento_id)
    clas = db.get(Clasificador, presupuesto.clasificador_id)
    uen = db.get(UnidadNegocio, presupuesto.unidad_negocio_id)

    return PresupuestoOut(
        **presupuesto.__dict__,
        departamento_nombre=dep.nombre if dep else None,
        clasificador_nombre=clas.nombre if clas else None,
        unidad_negocio_nombre=uen.nombre if uen else None
    )


# ---------------------------------------------------------
# 🗑️ ELIMINAR PRESUPUESTO
# ---------------------------------------------------------
@router.delete(
    "/{presupuesto_id}",
    status_code=204,
    summary="Eliminar presupuesto",
    description="Elimina un presupuesto existente."
)
def eliminar_presupuesto(presupuesto_id: int, db: Session = Depends(get_db)):
    """
    Elimina un presupuesto por su ID.
    """
    presupuesto = db.get(Presupuesto, presupuesto_id)
    if not presupuesto:
        raise HTTPException(404, "Presupuesto no encontrado")

    db.delete(presupuesto)
    db.commit()

    return None
