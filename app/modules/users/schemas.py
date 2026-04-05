from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.enums import Role, UserStatus


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    status: UserStatus
    created_at: str
    updated_at: str


class UserUpdate(BaseModel):
    role: Optional[Role] = None
    status: Optional[UserStatus] = None

    model_config = {"use_enum_values": True}