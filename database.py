import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Verifica conexiones “muertas”
    pool_recycle=3600        # Recicla conexiones cada hora (MySQL)
)


# Crea la fábrica de sesiones (Unidad de Trabajo)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para modelos ORM
Base = declarative_base()

# Dependencia para inyectar sesión por request en FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()