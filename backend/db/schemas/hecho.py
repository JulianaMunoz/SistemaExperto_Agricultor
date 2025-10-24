from pydantic import BaseModel

class HechoCreate(BaseModel):
    descripcion: str

class HechoResponse(HechoCreate):
    id: int

    class Config:
        orm_mode = True