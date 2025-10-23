from pydantic import BaseModel

class FactorCreate(BaseModel):
    nombre: str
    categoria: str 

class FactorResponse(FactorCreate):
    id: int

    class Config:
        orm_mode = True