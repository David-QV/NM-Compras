from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import UsuarioRol, Permiso

def validar_permiso(
    perfil_id: int,
    clasificador_id: int,
    departamento_id: int,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),
):
    user_id = user_data.get("sub")  # tomado del JWT
    roles = db.query(UsuarioRol).filter_by(usuario_id=user_id).all()

    if not roles:
        raise HTTPException(403, "El usuario no tiene roles asignados")

    rol_nombres = [r.rol for r in roles]

    tiene_permiso = (
        db.query(Permiso)
        .filter(
            Permiso.rol.in_(rol_nombres),
            Permiso.perfil_id == perfil_id,
            Permiso.clasificador_id == clasificador_id,
            Permiso.departamento_id == departamento_id,
        )
        .first()
    )

    if not tiene_permiso:
        raise HTTPException(403, "No tienes permisos para esta acción")
