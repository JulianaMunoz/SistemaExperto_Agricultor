from fastapi import Depends, FastAPI, HTTPException, status
from core.config import settings

#imports of our dbs main files
from core.session import engine
from core.base_class import Base 

#para testear la connection
import psycopg2
from psycopg2 import OperationalError

#modelos
from db.models.factor import Factor
from db.models.factor_hecho import FactorHecho
from db.models.hecho import Hecho
from db.models.usuario import Usuario

from passlib.context import CryptContext                      # Librería para encriptar contraseñas (bcrypt, sha256_crypt, etc.)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError     # Excepciones específicas de SQLAlchemy para manejar errores en DB 
from sqlalchemy import text    

from sqlalchemy.orm import Session
from core.deps import get_db

#inpot schemas
from db.schemas.factor import FactorCreate, FactorResponse
from db.schemas.usuario import CrearUsuario, LeerUsuario , ActualizarUsuario 

def test_connection():
    print("🧠 Probando conexión a la base de datos...")
    print("🔗 URL:", repr(settings.DATABASE_URL))  # repr para ver si hay comillas o caracteres extra

    try:
        # Intentar conectar
        conn = psycopg2.connect(settings.DATABASE_URL, sslmode="require", connect_timeout=5)
        print("✅ Conexión exitosa a la base de datos!")
        conn.close()
    except OperationalError as e:
        print("❌ Error al conectar con la base de datos:")
        print(e)

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("tablas creadas correctamente")
    
def start_application():
    app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)
    test_connection()
    create_tables()
    return app

app = start_application()

#creando factores
@app.post("/factores/", response_model=FactorResponse)
def create_factor(factor: FactorCreate, db: Session = Depends(get_db)):
    # Crear nuevo
    new_factor = Factor(nombre=factor.nombre, categoria=factor.categoria)
    db.add(new_factor)
    db.commit()
    db.refresh(new_factor)
    return new_factor









# GESTION DE USUARIOS

# ---- CONFIGURACIÓN DE CONTRASEÑAS ----
# Se crea un contexto de cifrado de contraseñas (por defecto con bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
try:
    # Se hace una prueba de cifrado rápida para validar que bcrypt funcione correctamente
    _ = pwd_context.hash("probe")  
except Exception as e:
    # Si bcrypt falla (común en Windows o Python 3.13), se usa sha256_crypt como alternativa
    print("⚠️ bcrypt falló, usando sha256_crypt como fallback:", repr(e))
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# Función auxiliar que recibe una contraseña y devuelve su versión cifrada
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ---- ENDPOINT DE SALUD ----
# Permite comprobar si la API y la base de datos están funcionando
@app.get("/health")
def health(db: Session = Depends(get_db)):    # obtiene una sesión de DB mediante la dependencia get_db
    db.execute(text("SELECT 1"))              # ejecuta una consulta simple para verificar conexión
    return {"ok": True, "db": "up"}           # devuelve respuesta positiva si todo está bien


# ---- ENDPOINT DE CREACIÓN DE USUARIOS ----
@app.post("/users", response_model=LeerUsuario, status_code=status.HTTP_201_CREATED)
def create_user(payload: CrearUsuario, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario en la base de datos.
    - Valida que el email y el nombre no estén duplicados.
    - Cifra la contraseña antes de guardar.
    - Maneja errores de integridad y base de datos.
    """

    try:
        # 1️⃣ Verificar si ya existe un usuario con el mismo email o nombre
        exists = db.query(Usuario).filter(
            (Usuario.email == payload.email) | (Usuario.name == payload.name)
        ).first()
        if exists:
            # Si existe, lanza error 400 (Bad Request)
            raise HTTPException(status_code=400, detail="Usuario ya existe (email o name)")

        # 2️⃣ Crear el nuevo objeto usuario con los datos validados
        user = Usuario(
            name=payload.name,
            email=payload.email,
            password=get_password_hash(payload.password),   # Contraseña cifrada
            is_active=True,
        )

        # 3️⃣ Guardar en la base de datos
        db.add(user)
        db.commit()     # Confirma la transacción
        db.refresh(user)  # Refresca el objeto para obtener su ID autogenerado
        return user

    # ---- MANEJO DE ERRORES ----
    except IntegrityError as ie:
        db.rollback()   # Revertir cambios si falla la integridad (p.ej., duplicado de email)
        print("IntegrityError:", repr(ie))
        raise HTTPException(status_code=400, detail="Violación de integridad (posible duplicado).")

    except SQLAlchemyError as se:
        db.rollback()   # Revertir cambios ante errores genéricos del motor SQL
        print("SQLAlchemyError:", repr(se))
        raise HTTPException(status_code=500, detail="Error de base de datos.")

    except Exception as e:
        db.rollback()   # Revertir en caso de errores inesperados (errores de Python, lógicos, etc.)
        print("Unhandled Exception:", repr(e))
        raise HTTPException(status_code=500, detail="Error interno del servidor.")

# --- helpers de password ---
def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False

# --- LOGIN ---
@app.post("/login", response_model=LeerUsuario)
def login(email: str, password: str, db: Session = Depends(get_db)):
    """
    Login básico SIN JWT:
    - Recibe email y password como query/body simple (puedes enviarlos como form-data, JSON o query).
    - Verifica credenciales y devuelve el usuario.
    """
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(password, user.password):
        # No reveles si falló el email o el password
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return user

# --- UPDATE parcial ---
@app.patch("/users/{user_id}", response_model=LeerUsuario)
def update_user(user_id: int, payload: ActualizarUsuario, db: Session = Depends(get_db)):
    """
    Actualiza campos opcionales: name, email, is_active, password.
    Valida colisión de email.
    """
    user = db.query(Usuario).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar email duplicado si viene en el payload
    if payload.email is not None:
        exists = db.query(Usuario).filter(
            Usuario.email == payload.email,
            Usuario.id != user_id
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email ya está en uso")
        user.email = payload.email

    if payload.name is not None:
        # opcional: validar colisión de name
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

# --- DELETE ---
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Elimina un usuario por id.
    """
    user = db.query(Usuario).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return None