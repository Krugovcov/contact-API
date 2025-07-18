from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSchema(BaseModel):
    username:str = Field( min_length=3, max_length=50)
    email : str = EmailStr
    password :str = Field( min_length=6, max_length=15)


class UserResponse(BaseModel):
    id: int = 1
    username: str
    email: EmailStr 
    avatar: str | None
    model_config = ConfigDict(from_attributes = True) 
    confirmed: bool = False

class TokenSchema(BaseModel):
    access_token:str
    refresh_token:str
    token_type: str = "bearer"

    
class RequestEmail(BaseModel):
    email: EmailStr