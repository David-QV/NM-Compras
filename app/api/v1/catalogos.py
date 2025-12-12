from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import UnidadNegocio, Articulo, Departamento, Proveedor, Clasificador
from app.schemas.catalogos import (
    UnidadNegocioCreate, UnidadNegocioOut,
    ArticuloCreate, ArticuloOut,
    DepartamentoCreate, DepartamentoOut,
    ClasificadorCreate, ClasificadorOut,
)

router = APIRouter(prefix="/api", tags=["Catálogos"])

# ---- UNIDADES DE NEGOCIO ----
@router.post("/unidades-negocio", response_model=UnidadNegocioOut)
def crear_unidad_negocio(payload: UnidadNegocioCreate, db: Session = Depends(get_db)):
    if db.query(UnidadNegocio).filter_by(nombre=payload.nombre).first():
        raise HTTPException(status_code=400, detail="Unidad de negocio ya existe")
    uen = UnidadNegocio(nombre=payload.nombre)
    db.add(uen)
    db.commit()
    db.refresh(uen)
    return uen

@router.get("/unidades-negocio", response_model=list[UnidadNegocioOut])
def listar_unidades_negocio(db: Session = Depends(get_db)):
    return db.query(UnidadNegocio).all()

# ---- CLASIFICADORES ----
@router.post("/clasificadores", response_model=ClasificadorOut)
def crear_clasificador(payload: ClasificadorCreate, db: Session = Depends(get_db)):
    if db.query(Clasificador).filter_by(nombre=payload.nombre).first():
        raise HTTPException(status_code=400, detail="Clasificador ya existe")
    nuevo = Clasificador(nombre=payload.nombre)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/clasificadores", response_model=list[ClasificadorOut])
def listar_clasificadores(db: Session = Depends(get_db)):
    return db.query(Clasificador).all()


# ---- ARTÍCULOS ----
@router.post("/articulos", response_model=ArticuloOut)
def crear_articulo(payload: ArticuloCreate, db: Session = Depends(get_db)):
    # Validar que el clasificador exista si se envía
    clasificador = None
    if payload.clasificador_id:
        clasificador = db.query(Clasificador).filter_by(id=payload.clasificador_id).first()
        if not clasificador:
            raise HTTPException(status_code=404, detail="Clasificador no encontrado")

    art = Articulo(nombre=payload.nombre, clasificador_id=payload.clasificador_id)
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


@router.get("/articulos", response_model=list[ArticuloOut])
def listar_articulos(db: Session = Depends(get_db)):
    return db.query(Articulo).all()


# ---- DEPARTAMENTOS ----
@router.post("/departamentos", response_model=DepartamentoOut)
def crear_departamento(payload: DepartamentoCreate, db: Session = Depends(get_db)):
    if db.query(Departamento).filter_by(nombre=payload.nombre).first():
        raise HTTPException(status_code=400, detail="Departamento ya existe")
    dep = Departamento(nombre=payload.nombre)
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.get("/departamentos", response_model=list[DepartamentoOut])
def listar_departamentos(db: Session = Depends(get_db)):
    return db.query(Departamento).all()


# ---- PROVEEDORES ----
@router.get("/proveedores")
def listar_proveedores(db: Session = Depends(get_db)):
    data = db.query(Proveedor).all()
    return [{"id": x.id, "nombre": x.nombre} for x in data]

@router.post("/proveedores")
def crear_proveedor(nombre: str, db: Session = Depends(get_db)):
    p = Proveedor(nombre=nombre)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "nombre": p.nombre}



