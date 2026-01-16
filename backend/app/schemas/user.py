from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.models.user import BaseCurrency


class UserBase(BaseModel):
    email: EmailStr
    name: str
    base_currency: BaseCurrency = BaseCurrency.KRW


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    base_currency: BaseCurrency | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
