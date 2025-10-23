# ------------------------------------------------------------------------------
# Este archivo define las dependencias de la aplicación.
# La función get_db() crea una sesión de base de datos para cada petición HTTP
# usando SQLAlchemy. Gracias a Depends(get_db), FastAPI inyecta automáticamente
# esta sesión en los endpoints que la necesiten y se encarga de cerrarla al final.
# Esto asegura un manejo limpio de las conexiones y evita fugas o bloqueos.
# ------------------------------------------------------------------------------
from core.session import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()