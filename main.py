# Importaciones principales de FastAPI y SQLAlchemy
from fastapi import FastAPI, Depends, HTTPException, status   # FastAPI base, manejo de dependencias, errores y códigos de estado
from sqlalchemy.orm import Session                            # Manejo de sesiones de base de datos
from sqlalchemy import text                                   # Permite ejecutar sentencias SQL directas (como SELECT 1)
from passlib.context import CryptContext                      # Librería para encriptar contraseñas (bcrypt, sha256_crypt, etc.)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError     # Excepciones específicas de SQLAlchemy para manejar errores en DB

# Importamos módulos propios del proyecto
from database import get_db, Base, engine                      # Conexión y configuración del motor SQL
import models, schemas                                         # Modelos ORM (tablas) y esquemas Pydantic (validación de datos)

# Crea las tablas definidas en los modelos si no existen
Base.metadata.create_all(bind=engine)

# Instancia principal de la aplicación FastAPI
app = FastAPI(title="Sistema Experto API")

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
@app.post("/users", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario en la base de datos.
    - Valida que el email y el nombre no estén duplicados.
    - Cifra la contraseña antes de guardar.
    - Maneja errores de integridad y base de datos.
    """

    try:
        # 1️⃣ Verificar si ya existe un usuario con el mismo email o nombre
        exists = db.query(models.User).filter(
            (models.User.email == payload.email) | (models.User.name == payload.name)
        ).first()
        if exists:
            # Si existe, lanza error 400 (Bad Request)
            raise HTTPException(status_code=400, detail="Usuario ya existe (email o name)")

        # 2️⃣ Crear el nuevo objeto usuario con los datos validados
        user = models.User(
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
@app.post("/login", response_model=schemas.UserRead)
def login(email: str, password: str, db: Session = Depends(get_db)):
    """
    Login básico SIN JWT:
    - Recibe email y password como query/body simple (puedes enviarlos como form-data, JSON o query).
    - Verifica credenciales y devuelve el usuario.
    """
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.password):
        # No reveles si falló el email o el password
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return user

# --- UPDATE parcial ---
@app.patch("/users/{user_id}", response_model=schemas.UserRead)
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)):
    """
    Actualiza campos opcionales: name, email, is_active, password.
    Valida colisión de email.
    """
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar email duplicado si viene en el payload
    if payload.email is not None:
        exists = db.query(models.User).filter(
            models.User.email == payload.email,
            models.User.id != user_id
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email ya está en uso")
        user.email = payload.email

    if payload.name is not None:
        # opcional: validar colisión de name
        exists_name = db.query(models.User).filter(
            models.User.name == payload.name,
            models.User.id != user_id
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
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return None
