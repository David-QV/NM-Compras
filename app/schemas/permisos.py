from pydantic import BaseModel

# --- Perfil ---
class PerfilBase(BaseModel):
    nombre: str

class PerfilCreate(PerfilBase):
    pass

class PerfilOut(PerfilBase):
    id: int
    class Config:
        from_attributes = True


# --- UsuarioRol ---
class UsuarioRolBase(BaseModel):
    usuario_id: int
    rol: str

class UsuarioRolCreate(UsuarioRolBase):
    pass

class UsuarioRolOut(UsuarioRolBase):
    id: int
    class Config:
        from_attributes = True


# --- Permiso ---
class PermisoBase(BaseModel):
    rol: str
    clasificador_id: int
    departamento_id: int
    perfil_id: int

class PermisoCreate(PermisoBase):
    pass

class PermisoOut(PermisoBase):
    id: int
    clasificador_nombre: str | None = None
    departamento_nombre: str | None = None
    perfil_nombre: str | None = None
    class Config:
        from_attributes = True
