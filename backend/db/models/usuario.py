from sqlalchemy import Column, Integer, Text, String, Boolean
from core.base_class import Base

class Usuario(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    password = Column(String(100), nullable=False)