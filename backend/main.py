from fastapi import Depends, FastAPI, HTTPException
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

from sqlalchemy.orm import Session
from core.deps import get_db
#schemas
from db.schemas.factor import FactorCreate, FactorResponse
from db.schemas.hecho import HechoCreate, HechoResponse
from db.schemas.factor_hecho import FactorHechoCreate, FactorHechoResponse


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