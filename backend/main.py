from fastapi import FastAPI
from core.config import settings

#imports of our dbs main files
from core.session import engine
from core.base_class import Base 

import psycopg2
from psycopg2 import OperationalError

from db.models.factor import Factor
from db.models.factor_hecho import Factor_hecho
from db.models.hecho import Hecho

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

# @app.get("/")
# def home():
#     return {"msg":"Hello FastAPI, DB initialized!"}