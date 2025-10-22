# schemas.py
# Esquemas de entrada/salida para validar y devolver datos seguros.

from pydantic import BaseModel, Field, EmailStr
from typing import Optional

# Lo que el cliente envía para registrarse
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6, max_length=128)

# Lo que el cliente envía para iniciar sesión
class UserLogin(BaseModel):
    username: str
    password: str

# Lo que devolvemos al cliente
class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool

    class Config:
        from_attributes = True  # permite devolver objetos ORM
