from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.base_class import Base

class Factor_hecho(Base):
    id = Column(Integer, primary_key=True)
    factor_id = Column(Integer, ForeignKey("factor.id"), nullable=False)
    hecho_id = Column(Integer, ForeignKey("hecho.id"), nullable=False)
    operador = Column(String, nullable=False)
    valor = Column(String, nullable=False)
    
    hecho = relationship("Hecho", back_populates="condiciones")
    factor = relationship("Factor", back_populates="condiciones")