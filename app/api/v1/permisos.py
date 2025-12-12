from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Permiso, UsuarioRol, Clasificador, Departamento, Perfil
from app.schemas.permisos import (
    PermisoCreate, PermisoOut,
    UsuarioRolCreate, UsuarioRolOut,
    PerfilCreate, PerfilOut
)

router = APIRouter(prefix="/api/permisos", tags=["Permisos"])

# ---------- PERFIL ----------
@router.post("/perfil", response_model=PerfilOut)
def crear_perfil(data: PerfilCreate, db: Session = Depends(get_db)):
    if db.query(Perfil).filter_by(nombre=data.nombre).first():
        raise HTTPException(400, "El perfil ya existe")
    perfil = Perfil(**data.model_dump())
    db.add(perfil)
    db.commit()
    db.refresh(perfil)
    return perfil

@router.get("/perfil", response_model=list[PerfilOut])
def listar_perfiles(db: Session = Depends(get_db)):
    return db.query(Perfil).order_by(Perfil.nombre).all()


# ---------- USUARIO_ROL ----------
@router.post("/usuario-rol", response_model=UsuarioRolOut)
def asignar_rol(data: UsuarioRolCreate, db: Session = Depends(get_db)):
    nuevo = UsuarioRol(**data.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.get("/usuario-rol", response_model=list[UsuarioRolOut])
def listar_roles_usuario(db: Session = Depends(get_db)):
    return db.query(UsuarioRol).all()


# ---------- PERMISOS ----------
@router.post("/", response_model=PermisoOut)
def crear_permiso(data: PermisoCreate, db: Session = Depends(get_db)):
    if not db.get(Clasificador, data.clasificador_id):
        raise HTTPException(400, "Clasificador no válido")
    if not db.get(Departamento, data.departamento_id):
        raise HTTPException(400, "Departamento no válido")
    if not db.get(Perfil, data.perfil_id):
        raise HTTPException(400, "Perfil no válido")

    permiso = Permiso(**data.model_dump())
    db.add(permiso)
    db.commit()
    db.refresh(permiso)
    return permiso


@router.get("/", response_model=list[PermisoOut])
def listar_permisos(db: Session = Depends(get_db)):
    permisos = db.query(Permiso).join(Clasificador).join(Departamento).join(Perfil).all()
    return [
        PermisoOut(
            id=p.id,
            rol=p.rol,
            clasificador_id=p.clasificador_id,
            departamento_id=p.departamento_id,
            perfil_id=p.perfil_id,
            clasificador_nombre=p.clasificador.nombre if p.clasificador else None,
            departamento_nombre=p.departamento.nombre if p.departamento else None,
            perfil_nombre=p.perfil.nombre if p.perfil else None,
        )
        for p in permisos
    ]
