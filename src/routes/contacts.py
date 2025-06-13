from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.database.db import get_db
from src.repository import contacts as repositories_contacts
from src.schemas.contact import ContactBookSchema, ContactBookSchemaUpdateSchema, ContactBookResponse
from src.services.auth import auth_service
from src.entity.models import User  # Типізація користувача

router = APIRouter(prefix='/contacts', tags=['contacts'])

@router.get('/birthday', response_model=list[ContactBookResponse])
async def birthday(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
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
    current_user: User = Depends(auth_service.get_current_user)
):
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
    return await repositories_contacts.create_contact(body, db, current_user.id)

@router.put('/{contact_id}', response_model=ContactBookResponse)
async def update_contact(
    body: ContactBookSchemaUpdateSchema,
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
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
    await repositories_contacts.delete_contact(contact_id, db, current_user.id)
