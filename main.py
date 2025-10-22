# main.py
# App FastAPI con endpoints de usuarios (registro y login) conectados a MySQL.

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import Base, engine, get_db
from models import User
from schemas import UserCreate, UserLogin, UserOut

# Crea tablas si no existen (en producción usa migraciones: Alembic)
Base.metadata.create_all(bind=engine)

# Contexto de hashing (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Sistema Experto Agricultor")

@app.get("/")
def read_root():
    # Respuesta simple para probar que el servicio está arriba
    return {"message": "Welcome to the Expert System for Farmers!"}

# Funciones utilitarias
def get_password_hash(password: str) -> str:
    """Genera hash seguro para la contraseña."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)

@app.post("/users/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un usuario nuevo:
    - Valida que username/email no estén en uso.
    - Guarda la contraseña hasheada (bcrypt).
    - Devuelve el usuario sin exponer la contraseña.
    """
    # ¿username ya existe?
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="El username ya está en uso.")

    # ¿email ya existe? (si se envió)
    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="El email ya está en uso.")

    # Crea la entidad
    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        is_active=True,
    )

    # Persiste en BD
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/users/login")
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Login básico (sin JWT por ahora):
    - Busca el usuario por username.
    - Verifica la contraseña con bcrypt.
    - Devuelve mensaje simple si es correcto.
    """
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas (usuario).")

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas (contraseña).")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo.")

    return {"message": "Login exitoso", "username": user.username}
