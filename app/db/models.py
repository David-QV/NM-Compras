from sqlalchemy import Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.base import Base

# ---- Catálogos ----

class UnidadNegocio(Base):
    __tablename__ = "unidad_negocio"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)


class Clasificador(Base):
    __tablename__ = "clasificador"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    articulos: Mapped[list["Articulo"]] = relationship(back_populates="clasificador_rel")


class Articulo(Base):
    __tablename__ = "articulo"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    clasificador_id: Mapped[int] = mapped_column(ForeignKey("clasificador.id"), nullable=True)

    clasificador_rel: Mapped["Clasificador"] = relationship(back_populates="articulos")


class Departamento(Base):
    __tablename__ = "departamento"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

class Proveedor(Base):
    __tablename__ = "proveedor"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)

# ---- Requerimientos ----
class Requerimiento(Base):
    __tablename__ = "requerimiento"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"), nullable=False)
    clasificador_id: Mapped[int] = mapped_column(ForeignKey("clasificador.id"), nullable=False)
    unidad_negocio_id: Mapped[int] = mapped_column(ForeignKey("unidad_negocio.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estatus: Mapped[str] = mapped_column(String(50), default="BORRADOR")

    departamento: Mapped["Departamento"] = relationship()
    clasificador: Mapped["Clasificador"] = relationship()
    unidad_negocio: Mapped["UnidadNegocio"] = relationship()
    items: Mapped[list["ReqItem"]] = relationship(back_populates="requerimiento", cascade="all, delete-orphan")


class ReqItem(Base):
    __tablename__ = "req_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requerimiento_id: Mapped[int] = mapped_column(ForeignKey("requerimiento.id"), nullable=False)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("articulo.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    requerimiento: Mapped["Requerimiento"] = relationship(back_populates="items")

# ---- Cotizaciones ----
class Cotizacion(Base):
    __tablename__ = "cotizacion"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requerimiento_id: Mapped[int] = mapped_column(ForeignKey("requerimiento.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estatus: Mapped[str] = mapped_column(String(50), default="ABIERTA")  # ABIERTA | APROBADA | RECHAZADA
    proveedores: Mapped[list["CotizacionProveedor"]] = relationship(back_populates="cotizacion", cascade="all, delete-orphan")

class CotizacionProveedor(Base):
    __tablename__ = "cotizacion_proveedor"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cotizacion_id: Mapped[int] = mapped_column(ForeignKey("cotizacion.id"), nullable=False)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedor.id"), nullable=False)
    cotizacion: Mapped["Cotizacion"] = relationship(back_populates="proveedores")
    items: Mapped[list["CotItem"]] = relationship(back_populates="cot_proveedor", cascade="all, delete-orphan")

class CotItem(Base):
    __tablename__ = "cot_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cotizacion_proveedor_id: Mapped[int] = mapped_column(ForeignKey("cotizacion_proveedor.id"), nullable=False)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("articulo.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unit: Mapped[float] = mapped_column(Float, nullable=False)
    cot_proveedor: Mapped["CotizacionProveedor"] = relationship(back_populates="items")

# ---- Órdenes de compra ----
class OrdenCompra(Base):
    __tablename__ = "orden_compra"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedor.id"), nullable=False)
    requerimiento_id: Mapped[int] = mapped_column(ForeignKey("requerimiento.id"), nullable=False)
    cotizacion_id: Mapped[int] = mapped_column(ForeignKey("cotizacion.id"), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estatus: Mapped[str] = mapped_column(String(50), default="BORRADOR")  # BORRADOR → EN_APROBACION → APROBADA...
    items: Mapped[list["OCItem"]] = relationship(back_populates="oc", cascade="all, delete-orphan")

class OCItem(Base):
    __tablename__ = "oc_item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    orden_compra_id: Mapped[int] = mapped_column(ForeignKey("orden_compra.id"), nullable=False)
    articulo_id: Mapped[int] = mapped_column(ForeignKey("articulo.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unit: Mapped[float] = mapped_column(Float, nullable=False)
    oc: Mapped["OrdenCompra"] = relationship(back_populates="items")

# ---- Autenticación y permisos ----
# --- Tabla de perfiles ---
class Perfil(Base):
    __tablename__ = "perfil"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    permisos = relationship("Permiso", back_populates="perfil")

# --- Relación usuario ↔ rol ---
class UsuarioRol(Base):
    __tablename__ = "usuario_rol"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(Integer, nullable=False)  # id del usuario del sistema principal
    rol: Mapped[str] = mapped_column(String(50), nullable=False)

# --- Permisos combinados ---
class Permiso(Base):
    __tablename__ = "permiso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rol: Mapped[str] = mapped_column(String(50), nullable=False)
    clasificador_id: Mapped[int] = mapped_column(ForeignKey("clasificador.id"), nullable=False)
    departamento_id: Mapped[int] = mapped_column(ForeignKey("departamento.id"), nullable=False)
    perfil_id: Mapped[int] = mapped_column(ForeignKey("perfil.id"), nullable=False)

    # Relaciones
    clasificador = relationship("Clasificador")
    departamento = relationship("Departamento")
    perfil = relationship("Perfil", back_populates="permisos")
    

