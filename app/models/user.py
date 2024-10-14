"""
Style for the pydantic models taken from FastAPI
creator tiangolo's project template in Github
https://tinyurl.com/3esb4r2j

Modified for my use
"""

from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from pydantic import Field
from pydantic import UUID4

from app.models.api_model import APIModel


# Shared properties
class UserName(APIModel):
    username: str = Field(..., max_length=150)


class UserBase(APIModel):
    user_uuid: UUID4
    username: str = Field(..., max_length=150)


# Properties to receive via API on creation
class UserCreate(UserName):
    password: str


class User(UserBase):
    email: Optional[EmailStr] = Field(None, exclusiveMaximum=255)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


# Additional properties stored in DB
class UserInDB(User):
    password: str
