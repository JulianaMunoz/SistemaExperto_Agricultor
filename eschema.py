from pydantic import BaseModel



class UserCreate(BaseModel):       #esquema de los qu espera fastapi para crear un usuario
    name: str
    email: str
    password: str

class UserRead(BaseModel):      #esquema de los qu espera fastapi para leer un usuario
    id: int
    name: str
    email: str
    is_active: bool
    
class UserUpdate(BaseModel):    #esquema de los qu espera fastapi para actualizar un usuario
    name: str | None = None
    email: str | None = None
    is_active: bool | None = None
    password: str | None = None

    class Config:               #hace que pydantic pueda trabajar con objetos ORM de SQLAlchemy
        orm_mode = True