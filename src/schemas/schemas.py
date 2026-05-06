from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from src.models.models import UserRole


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    role: UserRole = UserRole.simple

class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}