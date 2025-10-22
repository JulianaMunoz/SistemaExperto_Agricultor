import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Opcional si usas .env sin tu gestor de procesos:
# from dotenv import load_dotenv; load_dotenv()

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # definido en .env

engine = create_engine(DATABASE_URL)  # pool de conexiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia típica para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
