from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from core.base_class import Base

class Factor(Base):
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    condiciones = relationship("factor_hecho", back_populates="factor", cascade="all, delete-orphan")