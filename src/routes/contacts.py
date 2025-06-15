from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.repository import contacts as repositories_contacts
from src.schemas.contact import ContactBookSchema, ContactBookSchemaUpdateSchema, ContactBookResponse
from src.services.auth import auth_service
from src.entity.models import User  

router = APIRouter(prefix='/contacts', tags=['contacts'])

@router.get('/birthday', response_model=list[ContactBookResponse])
async def birthday(
   
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Retrieve a list of contacts with upcoming birthdays for the current user.

    Args:
        db (AsyncSession): The asynchronous database session dependency.
        current_user (User): The currently authenticated user dependency.

    Returns:
        List[Contact]: A list of contacts whose birthdays are approaching.
    """
    contacts = await repositories_contacts.get_contacts_birthday(db, current_user.id)
    return contacts

@router.get('/', response_model=list[ContactBookResponse])
async def get_contacts(
    limit: int = Query(10, ge=10, le=500), 
    offset: int = Query(0, ge=0),
    name: str = Query(None), 
    secondname: str = Query(None), 
    email: str = Query(None), 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)):

    """
    Retrieve a list of contacts with optional filtering and pagination.
    Args:
        limit (int, optional): Maximum number of contacts to return. Must be between 10 and 500. Defaults to 10.
        offset (int, optional): Number of contacts to skip before starting to collect the result set. Must be >= 0. Defaults to 0.
        name (str, optional): Filter contacts by first name. Defaults to None.
        secondname (str, optional): Filter contacts by second name. Defaults to None.
        email (str, optional): Filter contacts by email. Defaults to None.
        db (AsyncSession): Database session dependency.
        current_user (User): The currently authenticated user.
    Returns:
        List[Contact]: A list of contacts matching the filters and pagination.
    Raises:
        HTTPException: If an internal server error occurs.
    """
    
    try:
        return await repositories_contacts.get_contacts(limit, offset, db, name, secondname, email, current_user.id)
    except Exception as e:
        import logging
        logging.error(f"Error in get_contacts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get('/{contact_id}', response_model=ContactBookResponse)
async def get_contact_by_id(
    
    contact_id: int = Path(ge=1), 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Retrieve a contact by its unique ID for the current authenticated user.

    Args:
        contact_id (int): The unique identifier of the contact. Must be greater than or equal to 1.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (User): The currently authenticated user dependency.

    Returns:
        Contact: The contact object if found.

    Raises:
        HTTPException: If the contact is not found (404 error).
    """
    contact = await repositories_contacts.get_contact_by_id(contact_id, db, current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.post(
    '/',
    response_model=ContactBookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=3, seconds=60))]
)
async def create_contact(
    
    body: ContactBookSchema, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Creates a new contact for the current user.

    Args:
        body (ContactBookSchema): The data required to create a new contact.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (User): The currently authenticated user dependency.

    Returns:
        The created contact object.

    Raises:
        HTTPException: If the contact cannot be created due to validation or database errors.
    """
    return await repositories_contacts.create_contact(body, db, current_user.id)

@router.put('/{contact_id}', response_model=ContactBookResponse)
async def update_contact(
    
    body: ContactBookSchemaUpdateSchema,
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Update an existing contact for the current user.

    Args:
        body (ContactBookSchemaUpdateSchema): The data to update the contact with.
        contact_id (int): The ID of the contact to update. Must be greater than or equal to 1.
        db (AsyncSession): The database session dependency.
        current_user (User): The currently authenticated user.

    Returns:
        Contact: The updated contact object.

    Raises:
        HTTPException: If the contact with the given ID is not found (404).
    """
    contact = await repositories_contacts.update_contact(contact_id, body, db, current_user.id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.delete('/{contact_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
   
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Deletes a contact by its ID for the current authenticated user.

    Args:
        contact_id (int): The ID of the contact to delete. Must be greater than or equal to 1.
        db (AsyncSession): The asynchronous database session dependency.
        current_user (User): The currently authenticated user dependency.

    Returns:
        None

    Raises:
        HTTPException: If the contact does not exist or the user is not authorized to delete it.
    """
    
    await repositories_contacts.delete_contact(contact_id, db, current_user.id)
    

