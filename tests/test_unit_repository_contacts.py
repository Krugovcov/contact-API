from datetime import date
import unittest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User, ContactBook
from src.schemas.contact import ContactBookSchema, ContactBookSchemaUpdateSchema
from src.repository.contacts import get_contacts, get_contacts_birthday, get_contact_by_id, create_contact, update_contact, delete_contact
from sqlalchemy.engine import Result


class TestContactsRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.user = User(id=1, username="testuser", password="testpass", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)
                               
    async def test_get_contacts_basic(self):
        user = User(id=1)
        contacts = [
            ContactBook(id=1, name="Alice", secondname="Smith", email="alice@example.com", user_id=1),
            ContactBook(id=2, name="Bob", secondname="Jones", email="bob@example.com", user_id=1)
        ]

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = contacts

        mock_result = MagicMock(spec=Result)
        mock_result.scalars.return_value = mock_scalars

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await get_contacts(limit=10, offset=0, db=mock_db, user=user)
        self.assertEqual(result, contacts)

    async def test_get_contacts_with_filters(self):
        user = User(id=1)
        contacts = [
            ContactBook(id=1, name="Alice", secondname="Smith", email="abracadabra@example.com", user_id=1)]
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = contacts
        mock_result = MagicMock(spec=Result)
        mock_result.scalars.return_value = mock_scalars
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        result = await get_contacts(limit=10, offset=0, db=mock_db, user=user, name="Alice", secondname=None, email="abracadabra@example.com")
        self.assertEqual(result, contacts)

    async def test_create_contact(self):
        body = ContactBookSchema(
            name="Alice",
            secondname="Smith",
            phone="+1234567890",  
            email="valid@example.com",  
            born_day=date(2000, 4, 30), 
            additional_data=None
        )
        result = await create_contact(body, self.session, self.user)
        self.assertIsInstance(result, ContactBook)

    async def test_update_contact(self):
        body = ContactBookSchemaUpdateSchema(
            name="Alex",
            secondname="Smith",
            phone="+1234567890",  
            email="valid@example.com",  
            born_day=date(1999, 4, 7), 
            additional_data=None
        )
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = ContactBook(id=1, name="Alice", secondname="Smith", email="abracadabra@example.com", user_id=1)
        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, body, self.session, self.user.id)
        self.assertIsInstance(result, ContactBook)
        self.assertEqual(result.name, body.name)
        self.assertEqual(result.secondname, body.secondname)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.born_day, body.born_day)

    async def test_delete_contact(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = ContactBook(id=1, name="Alice", secondname="Smith", email="abracadabra@example.com", user_id=self.user.id)
        self.session.execute.return_value = mocked_contact
        result = await delete_contact(1, self.session, self.user.id)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()

        self.assertIsInstance(result, ContactBook)

    async def test_get_contacts_birthday_None(self):
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = ContactBook(id=1, name="Alex",
            secondname="Smith",
            phone="+1234567890",  
            email="valid@example.com",  
            born_day=date(1999, 4, 7), 
            additional_data=None,
            user_id=self.user.id)
        self.session.execute.return_value = mocked_contact
        result = await get_contacts_birthday(self.session, self.user.id)
        self.assertEqual(len(result), 0)
        

    async def test_get_contacts_birthday(self):

        test_contact = ContactBook(
            id=1,
            name="Alex",
            secondname="Smith",
            phone="+1234567890",
            email="valid@example.com",
            born_day=date(1999, 6, 21),  
            additional_data=None,
            user_id=self.user.id
        )
        

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [test_contact]  
        
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        
        self.session.execute.return_value = mock_result
    
        result = await get_contacts_birthday(self.session, self.user.id)
        
     
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Alex")
        self.assertEqual(result[0].secondname, "Smith")
        self.assertEqual(result[0].phone, "+1234567890")

    