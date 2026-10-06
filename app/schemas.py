from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Wallet Schemas
class WalletResponse(BaseModel):
    id: int
    user_id: int
    balance: float
    currency: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionBase(BaseModel):
    receiver_id: int
    amount: float
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    amount: float
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionHistoryResponse(BaseModel):
    sent: list[TransactionResponse]
    received: list[TransactionResponse]


# Auth Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None
