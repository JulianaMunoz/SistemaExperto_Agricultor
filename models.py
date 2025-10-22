from sqlalchemy import create_engine, Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    role = Column(Boolean, default=False)
    password = Column(String)
    #encriptar la contraseña
Base.metadata.create_all(bind=create_engine('sqlite:///./test.db'))