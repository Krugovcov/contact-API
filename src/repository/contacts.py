from datetime import date, datetime, timedelta
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import ContactBook
from src.schemas.contact import ContactBookSchema, ContactBookSchemaUpdateSchema



async def get_contacts(limit: int, offset: int, db: AsyncSession, name: str = None, secondname: str = None, email: str = None, user_id: int = None):
    stmt = select(ContactBook).offset(offset).limit(limit)
    
    if user_id is not None:
        stmt = stmt.filter(ContactBook.user_id == user_id)
    if name:
        stmt = stmt.filter(ContactBook.name.ilike(f'%{name}%'))
    if secondname:
        stmt = stmt.filter(ContactBook.secondname.ilike(f'%{secondname}%'))
    if email:
        stmt = stmt.filter(ContactBook.email.ilike(f'%{email}%'))
        
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_contacts_birthday(db: AsyncSession, user_id: int):
    """
    Short summary of the function.

    Args:
        db (AsyncSession): Database session.
        user_id (int): ID of the user.

    Returns:
        ReturnType: Description of the return value.
    """
    today = datetime.today().date()
    seven_days_later = today + timedelta(days=7)
    
    stmt = select(ContactBook).filter(
        ContactBook.user_id == user_id,
        or_(
            # Коли період не переходить через новий рік
            (ContactBook.born_day >= today) & (ContactBook.born_day <= seven_days_later),
            # Коли період переходить через новий рік (декабрь-січень)
            (ContactBook.born_day >= date(today.year, 1, 1)) & 
            (ContactBook.born_day <= date(today.year, 1, 7)) & 
            (today.month == 12)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_contact_by_id(contact_id: int, db: AsyncSession, user_id: int):
    
    stmt = select(ContactBook).filter_by(id=contact_id, user_id=user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_contact(body: ContactBookSchema, db: AsyncSession, user_id: int):
    contact_data = body.model_dump(exclude_unset=True)
    contact_data['user_id'] = user_id  
    contact = ContactBook(**contact_data)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactBookSchemaUpdateSchema, db: AsyncSession, user_id: int):
    stmt = select(ContactBook).filter_by(id=contact_id, user_id=user_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        update_data = body.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contact, key, value)
        await db.commit()
        await db.refresh(contact)
    return contact
    


async def delete_contact(contact_id: int, db: AsyncSession, user_id: int):
    stmt = select(ContactBook).filter_by(id=contact_id, user_id=user_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact