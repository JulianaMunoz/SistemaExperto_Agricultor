from fastapi import Depends, FastAPI, HTTPException, status, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import EmailStr

from core.config import settings

# DB core
from core.session import engine
from core.base_class import Base

# Test de conexión
import psycopg2
from psycopg2 import OperationalError

# Modelos
from db.models.factor import Factor
from db.models.factor_hecho import FactorHecho
from db.models.hecho import Hecho
from db.models.usuario import Usuario

# Utilidades de seguridad y DB
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import text
from sqlalchemy.orm import Session
from core.deps import get_db

#schemas
from db.schemas.factor import FactorCreate, FactorResponse
from db.schemas.hecho import HechoCreate, HechoResponse
from db.schemas.factor_hecho import FactorHechoCreate, FactorHechoResponse
from db.schemas.usuario import CrearUsuario, LeerUsuario, ActualizarUsuario


# -------------------- utilidades de arranque --------------------
def test_connection():
    print("🧠 Probando conexión a la base de datos...")
    print("🔗 URL:", repr(settings.DATABASE_URL))
    try:
        conn = psycopg2.connect(settings.DATABASE_URL, sslmode="require", connect_timeout=5)
        print("✅ Conexión exitosa a la base de datos!")
        conn.close()
    except OperationalError as e:
        print("❌ Error al conectar con la base de datos:")
        print(e)

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("🧱 Tablas creadas correctamente")

def start_application():
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    test_connection()
    create_tables()
    return app


app = start_application()

# Ajusta esta ruta a tu estructura real si lo prefieres relativo
templates = Jinja2Templates(directory="C:\\Users\\Usuario\\SistemaExperto_Agricultor\\templates")


# -------------------- vistas HTML --------------------
@app.get("/", response_model=None)
def read_root(request: Request):
    # index.html: tu página de login con Bootstrap + JS
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Sistema Experto para Asistencia en la Elección de Cultivos"}
    )

@app.get("/register", response_model=None)
def register_page(request: Request):
    # register.html: tu página de registro con Bootstrap + JS
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "title": "Crear cuenta"}
    )
    
@app.get("/home", response_model=None)
def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "title": "Inicio"})



# -------------------- endpoints de prueba y dominio --------------------
@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True, "db": "up"}


# -------------------- FACTORES --------------------
@app.post("/factores/", response_model=FactorResponse)
def create_factor(factor: FactorCreate, db: Session = Depends(get_db)):
    new_factor = Factor(nombre=factor.nombre, categoria=factor.categoria)
    db.add(new_factor)
    db.commit()
    db.refresh(new_factor)
    return new_factor

#Creando Hechos
@app.post("/hechos/", response_model=HechoResponse)
def create_hecho(hecho: HechoCreate, db: Session = Depends(get_db)):
    # Crear nuevo
    new_hecho = Hecho(descripcion=hecho.descripcion)
    db.add(new_hecho)
    db.commit()
    db.refresh(new_hecho)
    return new_hecho

#Creando Reglas
@app.post("/reglas/", response_model=FactorHechoResponse)
def create_regla(factorHecho: FactorHechoCreate, db: Session = Depends(get_db)):
    # Crear nuevo
    new_regla = FactorHecho(factor_id=factorHecho.factor_id,hecho_id=factorHecho.hecho_id,operador=factorHecho.operador,valor=factorHecho.valor)
    db.add(new_regla)
    db.commit()
    db.refresh(new_regla)
    return new_regla

# -------------------- GESTIÓN DE USUARIOS --------------------
# Configuración de contraseñas (bcrypt con fallback)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
try:
    _ = pwd_context.hash("probe")
except Exception as e:
    print("⚠️ bcrypt falló, usando sha256_crypt como fallback:", repr(e))
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# ---- lógica central para crear usuario (reutilizable) ----
def create_user_core(payload: CrearUsuario, db: Session) -> Usuario:
    # Verificar duplicados por email o name
    exists = db.query(Usuario).filter(
        (Usuario.email == payload.email) | (Usuario.name == payload.name)
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Usuario ya existe (email o name)")

    user = Usuario(
        name=payload.name,
        email=payload.email,
        password=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---- creación vía JSON (API) ----
@app.post("/users", response_model=LeerUsuario, status_code=status.HTTP_201_CREATED)
def create_user(payload: CrearUsuario, db: Session = Depends(get_db)):
    try:
        return create_user_core(payload, db)
    except IntegrityError as ie:
        db.rollback()
        print("IntegrityError:", repr(ie))
        raise HTTPException(status_code=400, detail="Violación de integridad (posible duplicado).")
    except SQLAlchemyError as se:
        db.rollback()
        print("SQLAlchemyError:", repr(se))
        raise HTTPException(status_code=500, detail="Error de base de datos.")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Unhandled Exception:", repr(e))
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


# ---- creación vía FORM-DATA (desde register.html) ----
@app.post("/users-form", response_model=LeerUsuario, status_code=status.HTTP_201_CREATED)
def create_user_form(
    name: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        payload = CrearUsuario(name=name, email=email, password=password)
        return create_user_core(payload, db)
    except IntegrityError as ie:
        db.rollback()
        print("IntegrityError:", repr(ie))
        raise HTTPException(status_code=400, detail="Violación de integridad (posible duplicado).")
    except SQLAlchemyError as se:
        db.rollback()
        print("SQLAlchemyError:", repr(se))
        raise HTTPException(status_code=500, detail="Error de base de datos.")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("Unhandled Exception:", repr(e))
        raise HTTPException(status_code=500, detail="Error interno del servidor.")


# ---- LOGIN por form-data (desde index.html) ----
@app.post("/login", response_model=LeerUsuario)
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(password, user.password):
        # Sin revelar qué falló
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return user


# ---- UPDATE parcial ----
@app.patch("/users/{user_id}", response_model=LeerUsuario)
def update_user(user_id: int, payload: ActualizarUsuario, db: Session = Depends(get_db)):
    # Usar db.get() (SQLAlchemy 2.x) si lo tienes disponible
    user = db.get(Usuario, user_id) if hasattr(db, "get") else db.query(Usuario).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.email is not None:
        exists = db.query(Usuario).filter(
            Usuario.email == payload.email,
            Usuario.id != user_id
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email ya está en uso")
        user.email = payload.email

    if payload.name is not None:
        exists_name = db.query(Usuario).filter(
            Usuario.name == payload.name,
            Usuario.id != user_id
        ).first()
        if exists_name:
            raise HTTPException(status_code=400, detail="Nombre ya está en uso")
        user.name = payload.name

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.password is not None:
        user.password = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)
    return user


# ---- DELETE ----
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(Usuario, user_id) if hasattr(db, "get") else db.query(Usuario).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return None
