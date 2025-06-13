from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase
from datetime import date 
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class ContactBook(Base):
    __tablename__ = 'contacts'
    id: Mapped[int] = mapped_column(primary_key = True)
    name:Mapped[str] = mapped_column(String(50))
    secondname: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(50), nullable=True)
    born_day: Mapped[date] = mapped_column(default=None, nullable=True)
    additional_data: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user = relationship("User", back_populates="contacts")


class User(Base):
    __tablename__ = 'users'
    id:Mapped[int] = mapped_column(primary_key = True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)

    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True) 
 
    created_at:Mapped[date] = mapped_column('created_at', DateTime, default=func.now())
    updated_at:Mapped[date] = mapped_column('updated_at', DateTime, default=func.now(), onupdate=func.now())

    confirmed: Mapped[bool] = mapped_column('confirmed', default=False, nullable=True)
    contacts = relationship("ContactBook", back_populates="user")