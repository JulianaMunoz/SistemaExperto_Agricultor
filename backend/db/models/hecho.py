from sqlalchemy import Column, Integer, Text
from sqlalchemy.orm import relationship
from core.base_class import Base

class Hecho(Base):
    id = Column(Integer, primary_key=True)
    descripcion = Column(Text, nullable=False)
    condiciones = relationship("factor_hecho", back_populates="hecho", cascade="all, delete-orphan")