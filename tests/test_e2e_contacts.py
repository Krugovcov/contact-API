from unittest.mock import MagicMock, patch
from src.conf import messages
from src.services.auth import auth_service

def test_get_contacts(client, get_token):
    with patch.object(auth_service, 'cache', new=MagicMock()) as redis_mock:
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/contacts", headers=headers)
        
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0 
        assert data is not None

def test_create_contact(client, get_token, monkeypatch):
    with patch.object(auth_service, 'cache') as redis_mock:
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("api/contacts", headers=headers, json={
            "name": "Alice",
            "secondname": "Smith",
            "phone": "+1234567890",
            "email": "alic33e@meta.ua",
            "additional_data": None
        })
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["name"] == "Alice"
        assert data["secondname"] == "Smith"
        assert data["phone"] == "+1234567890"
        assert data["email"] == "alic33e@meta.ua"
        assert data["additional_data"] is None

def test_get_contact_by_id(client, get_token):
    with patch.object(auth_service, 'cache', new=MagicMock()) as redis_mock:
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/contacts/1", headers=headers)
        
        assert response.status_code == 200, response.text
        data = response.json()
      
def test_get_wrong_contact_by_id(client, get_token):
    with patch.object(auth_service, 'cache', new=MagicMock()) as redis_mock:
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/contacts/2", headers=headers)
        
        assert response.status_code == 404, response.text
        data = response.json()
        assert data["detail"] == messages.CONTACT_NOT_FOUND

def test_update_contact(client, get_token):
    with patch.object(auth_service, 'cache', new=MagicMock()) as redis_mock:
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.put("/api/contacts/1", headers=headers, json={
            "name": "Alice",
            "secondname": "Johnson",
            "phone": "+1234567890",
            "email": "abracadabra@aexampple.com",
            "additional_data": None})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["name"] == "Alice"
        assert data["secondname"] == "Johnson"
        assert data["phone"] == "+1234567890"
        assert data["email"] == "abracadabra@aexampple.com"

def test_delete_contact(client, get_token):
    with patch.object(auth_service, 'cache', new=MagicMock()) as redis_mock:
        redis_mock.get.return_value = None
        token = get_token
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.delete("/api/contacts/1", headers=headers)
        
        assert response.status_code == 204, response.text
        assert response.content == b""
        