from datetime import datetime
from typing import Optional

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

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserPasswordChange(BaseModel):
    new_password: str = Field(..., min_length=6)


# Categories schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None

class CategoryRead(CategoryBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class CategoryWithProducts(CategoryRead):
    products: list["ProductRead"] = []


# products schemas
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    category_id: int
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    note_general: Optional[str] = None
    note_special: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=256)
    category_id: Optional[int] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    note_general: Optional[str] = None
    note_special: Optional[str] = None

class ProductRead(BaseModel):
    id: int
    name: str
    category_id: int
    category_name: Optional[str] = None
    description: Optional[str] = None
    price: float
    note_general: Optional[str] = None
    note_special: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# currencty schemas
class CurrencyRate(BaseModel):
    currency: str
    rate: float
    price_usd: float


CategoryWithProducts.model_rebuild()
