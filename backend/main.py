from fastapi import FastAPI
from core.config import settings

#imports of our dbs main files
from db.session import engine
from db.base_class import Base 

def create_tables():
    Base.metadata.create_all(bind=engine)
    
def start_application():
    app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)
    create_tables()
    return app

app = start_application()

@app.get("/")
def home():
    return {"msg":"Hola Mundo"}