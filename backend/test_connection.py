import psycopg2
from psycopg2 import OperationalError
from core.config import settings  # ajusta el import según tu estructura real (por ejemplo: from config import settings)
from core.session import engine
from core.base_class import Base
from db.models.factor import Factor 

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("tabla creada correctamente")

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

if __name__ == "__main__":
    test_connection()
    create_tables()
