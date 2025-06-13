from typing import Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field

class ContactBookSchema(BaseModel):
    name:str = Field( min_length=3, max_length=50)
    secondname : str = Field(min_length=3, max_length=250)
    phone : Optional[str] = Field(min_length=3, max_length=20)
    email: Optional[EmailStr] = Field(max_length=50, nullable=True)
    born_day: Optional[date] = None
    additional_data: Optional[str] = Field(max_length=100, nullable=True)

class ContactBookSchemaUpdateSchema(BaseModel):
    name:Optional[str] = Field( min_length=3, max_length=50)
    secondname : Optional[str] = Field(min_length=3, max_length=250)
    phone : Optional[str] = Field(min_length=3, max_length=20)
    email: Optional[EmailStr] = Field(max_length=50, nullable=True)
    born_day: Optional[date] = None
    additional_data: Optional[str] = Field(max_length=100, nullable=True)

class ContactBookResponse(BaseModel):
    id: int
    name: str
    secondname: str
    phone: Optional[str]
    email: Optional[EmailStr]
    born_day: Optional[date]
    additional_data: Optional[str]

    class Config:
        from_attributes = True
        orm_mode = True
