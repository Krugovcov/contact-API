from datetime import date, datetime, timedelta
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import ContactBook, User
from src.schemas.contact import ContactBookSchema, ContactBookSchemaUpdateSchema



async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User, name: str = None, secondname: str = None, email: str = None, user_id: int = None):
    """
    Retrieve a list of contacts from the database with optional filtering and pagination.
    Args:
        limit (int): The maximum number of contacts to return.
        offset (int): The number of contacts to skip before starting to collect the result set.
        db (AsyncSession): The asynchronous database session to use for the query.
        name (str, optional): Filter contacts by name (case-insensitive, partial match).
        secondname (str, optional): Filter contacts by second name (case-insensitive, partial match).
        email (str, optional): Filter contacts by email (case-insensitive, partial match).
        user_id (int, optional): Filter contacts by the associated user ID.
    Returns:
        List[ContactBook]: A list of contacts matching the specified filters and pagination.
    """
    stmt = select(ContactBook).filter(ContactBook.user_id == user.id)
    if user_id is not None:
        stmt = stmt.filter(ContactBook.user_id == user_id)
    if name:
        stmt = stmt.filter(ContactBook.name.ilike(f'%{name}%'))
    if secondname:
        stmt = stmt.filter(ContactBook.secondname.ilike(f'%{secondname}%'))
    if email:
        stmt = stmt.filter(ContactBook.email.ilike(f'%{email}%'))
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_contacts_birthday(db: AsyncSession, user_id: int):
    """
    Retrieve contacts from the database whose birthdays fall within the next 7 days for a specific user.
    Args:
        db (AsyncSession): The asynchronous database session.
        user_id (int): The ID of the user whose contacts are being queried.
    Returns:
        List[ContactBook]: A list of ContactBook objects representing contacts with upcoming birthdays.
    Notes:
        - Handles the case where the 7-day period crosses over the end of the year (December to January).
        - Assumes that the ContactBook model has a 'born_day' attribute of type date.
    """
    
    today = datetime.today().date()
    seven_days_later = today + timedelta(days=7)
    
    stmt = select(ContactBook).filter(
        ContactBook.user_id == user_id,
        or_(
            (ContactBook.born_day >= today) & (ContactBook.born_day <= seven_days_later),
            (ContactBook.born_day >= date(today.year, 1, 1)) & 
            (ContactBook.born_day <= date(today.year, 1, 7)) & 
            (today.month == 12)
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_contact_by_id(contact_id: int, db: AsyncSession, user_id: int):
    """
    Retrieve a contact by its ID for a specific user.
    Args:
        contact_id (int): The unique identifier of the contact to retrieve.
        db (AsyncSession): The asynchronous database session to use for the query.
        user_id (int): The ID of the user who owns the contact.
    Returns:
        ContactBook or None: The contact object if found, otherwise None.
    """
    
    stmt = select(ContactBook).filter_by(id=contact_id, user_id=user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_contact(body: ContactBookSchema, db: AsyncSession, user_id: int):
    """
    Asynchronously creates a new contact record in the database for a specified user.

    Args:
        body (ContactBookSchema): The schema object containing contact details to be created.
        db (AsyncSession): The asynchronous database session used for database operations.
        user_id (int): The ID of the user to whom the contact will be associated.

    Returns:
        ContactBook: The newly created contact instance with updated fields from the database.

    Raises:
        SQLAlchemyError: If there is an error during the database transaction.
    """
    contact_data = body.model_dump(exclude_unset=True)
    contact_data['user_id'] = user_id  
    contact = ContactBook(**contact_data)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactBookSchemaUpdateSchema, db: AsyncSession, user_id: int):
    """
    Asynchronously updates an existing contact in the database for a specific user.

    Args:
        contact_id (int): The unique identifier of the contact to update.
        body (ContactBookSchemaUpdateSchema): The schema containing the fields to update.
        db (AsyncSession): The asynchronous database session.
        user_id (int): The unique identifier of the user who owns the contact.

    Returns:
        ContactBook or None: The updated contact object if found and updated, otherwise None.
    """
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
    """
    Asynchronously deletes a contact from the database for a specific user.

    Args:
        contact_id (int): The ID of the contact to be deleted.
        db (AsyncSession): The asynchronous database session.
        user_id (int): The ID of the user who owns the contact.

    Returns:
        ContactBook or None: The deleted contact object if found and deleted, otherwise None.
    """
    stmt = select(ContactBook).filter_by(id=contact_id, user_id=user_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact