from pydantic import BaseModel, EmailStr, ConfigDict

class CrearUsuario(BaseModel):
    name: str
    email: EmailStr
    password: str

class LeerUsuario(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class ActualizarUsuario(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    password: str | None = None
    model_config = ConfigDict(from_attributes=True)