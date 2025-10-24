from pydantic import BaseModel

class FactorHechoCreate(BaseModel):
    factor_id: int
    hecho_id: int
    operador: str
    valor: str

class FactorHechoResponse(FactorHechoCreate):
    id: int

    class Config:
        orm_mode = True