from fastapi import Depends, FastAPI, HTTPException, status, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import psycopg2
from psycopg2 import OperationalError

# ---- Configuración base ----
from core.config import settings
from core.session import engine
from core.base_class import Base
from core.deps import get_db

# ---- Modelos ----
from db.models.factor import Factor
from db.models.hecho import Hecho
from db.models.factor_hecho import FactorHecho
from db.models.usuario import Usuario

# ---- Schemas ----
from db.schemas.factor import FactorCreate, FactorResponse
from db.schemas.hecho import HechoCreate, HechoResponse
from db.schemas.factor_hecho import FactorHechoCreate, FactorHechoResponse
from db.schemas.usuario import CrearUsuario, LeerUsuario, ActualizarUsuario


# ============================================================
#              INICIALIZACIÓN Y ARRANQUE DE APP
# ============================================================
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
templates = Jinja2Templates(directory="../templates")


# ============================================================
#                     VISTAS HTML
# ============================================================
@app.get("/", response_model=None)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Sistema Experto para Asistencia en la Elección de Cultivos"}
    )

@app.get("/register", response_model=None)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "title": "Crear cuenta"})

@app.get("/home", response_model=None)
def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "title": "Inicio"})

@app.get("/vista/recomendaciones", response_model=None)
def vista_recomendaciones(request: Request):
    return templates.TemplateResponse("recomendaciones.html", {"request": request, "title": "Recomendaciones"})


# ============================================================
#                     ENDPOINTS DE NEGOCIO
# ============================================================
@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True, "db": "up"}

# ---------- FACTORES ----------
@app.post("/factores/", response_model=FactorResponse)
def create_factor(factor: FactorCreate, db: Session = Depends(get_db)):
    new_factor = Factor(nombre=factor.nombre, categoria=factor.categoria)
    db.add(new_factor)
    db.commit()
    db.refresh(new_factor)
    return new_factor

# ---------- HECHOS ----------
@app.post("/hechos/", response_model=HechoResponse)
def create_hecho(hecho: HechoCreate, db: Session = Depends(get_db)):
    new_hecho = Hecho(descripcion=hecho.descripcion)
    db.add(new_hecho)
    db.commit()
    db.refresh(new_hecho)
    return new_hecho

# ---------- FACTOR-HECHO ----------
@app.post("/reglas/", response_model=FactorHechoResponse)
def create_regla(fh: FactorHechoCreate, db: Session = Depends(get_db)):
    new_regla = FactorHecho(
        factor_id=fh.factor_id, hecho_id=fh.hecho_id, operador=fh.operador, valor=fh.valor
    )
    db.add(new_regla)
    db.commit()
    db.refresh(new_regla)
    return new_regla


# ============================================================
#            NUEVA RUTA: FACTORES + VALORES (hechos)
# ============================================================
@app.get("/factors-values", response_model=None)
def get_factors_values(db: Session = Depends(get_db)):
    """
    Devuelve cada Factor con sus valores (columna 'valor') 
    provenientes de FactorHecho.
    """
    rows = (
        db.query(
            Factor.id.label("factor_id"),
            Factor.nombre.label("factor_nombre"),
            FactorHecho.id.label("factor_hecho_id"),
            FactorHecho.valor.label("valor"),
        )
        .join(FactorHecho, FactorHecho.factor_id == Factor.id)
        .order_by(Factor.nombre.asc(), FactorHecho.id.asc())
        .all()
    )

    agrupado = defaultdict(list)
    for r in rows:
        agrupado[r.factor_id].append({
            "factor_hecho_id": r.factor_hecho_id,
            "valor": r.valor
        })

    data = []
    for fid, valores in agrupado.items():
        nombre = next((r.factor_nombre for r in rows if r.factor_id == fid), f"Factor {fid}")
        data.append({
            "factor_id": fid,
            "factor_nombre": nombre,
            "valores": valores
        })

    return data


# ============================================================
#              AUTENTICACIÓN Y GESTIÓN DE USUARIOS
# ============================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
try:
    _ = pwd_context.hash("probe")
except Exception as e:
    print("⚠️ bcrypt falló, usando sha256_crypt:", repr(e))
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_user_core(payload: CrearUsuario, db: Session) -> Usuario:
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


@app.post("/users", response_model=LeerUsuario, status_code=status.HTTP_201_CREATED)
def create_user(payload: CrearUsuario, db: Session = Depends(get_db)):
    try:
        return create_user_core(payload, db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Violación de integridad (duplicado).")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de base de datos.")


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
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Violación de integridad (duplicado).")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de base de datos.")


@app.post("/login", response_model=LeerUsuario)
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return user


@app.patch("/users/{user_id}", response_model=LeerUsuario)
def update_user(user_id: int, payload: ActualizarUsuario, db: Session = Depends(get_db)):
    user = db.query(Usuario).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if payload.email and db.query(Usuario).filter(Usuario.email == payload.email, Usuario.id != user_id).first():
        raise HTTPException(status_code=400, detail="Email ya en uso")

    if payload.name and db.query(Usuario).filter(Usuario.name == payload.name, Usuario.id != user_id).first():
        raise HTTPException(status_code=400, detail="Nombre ya en uso")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(Usuario).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return None
