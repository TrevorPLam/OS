"""
Example: Django ViewSet Test Pattern
File: tests/api/clients/test_client_viewset.py
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from modules.firm.models import Firm
from modules.clients.models import Client
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def firm():
    """Create a test firm."""
    return Firm.objects.create(name='Test Firm', slug='test-firm')


@pytest.fixture
def user(firm):
    """Create a test user associated with firm."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    user.firm = firm
    user.save()
    return user


@pytest.fixture
def api_client(user, firm):
    """Create authenticated API client with firm context."""
    client = APIClient()
    client.force_authenticate(user=user)
    # Set firm on request (FirmScopedMixin uses request.firm)
    client.force_authenticate(firm=firm)
    return client


@pytest.fixture
def client(firm):
    """Create a test client."""
    return Client.objects.create(firm=firm, name='Test Client')


@pytest.mark.django_db
class TestClientViewSet:
    """Test suite for ClientViewSet."""

    def test_list_clients(self, api_client, firm, client):
        """Test listing clients (firm-scoped)."""
        response = api_client.get('/api/clients/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Client'

    def test_create_client(self, api_client, firm):
        """Test creating a new client."""
        data = {'name': 'New Client', 'firm': firm.id}
        response = api_client.post('/api/clients/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Client'
        assert Client.objects.filter(firm=firm, name='New Client').exists()

    def test_retrieve_client(self, api_client, client):
        """Test retrieving a single client."""
        response = api_client.get(f'/api/clients/{client.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Client'

    def test_update_client(self, api_client, client):
        """Test updating a client."""
        data = {'name': 'Updated Client'}
        response = api_client.patch(f'/api/clients/{client.id}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Client'
        client.refresh_from_db()
        assert client.name == 'Updated Client'

    def test_delete_client(self, api_client, client):
        """Test deleting a client."""
        response = api_client.delete(f'/api/clients/{client.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Client.objects.filter(id=client.id).exists()

    def test_firm_scoping(self, api_client, firm):
        """Test that clients are scoped to firm."""
        # Create client in different firm
        other_firm = Firm.objects.create(name='Other Firm', slug='other-firm')
        Client.objects.create(firm=other_firm, name='Other Client')

        # Create client in current firm
        Client.objects.create(firm=firm, name='My Client')

        # List should only return clients from current firm
        response = api_client.get('/api/clients/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'My Client'

    def test_unauthenticated_access(self, client):
        """Test that unauthenticated requests are rejected."""
        client = APIClient()
        response = client.get('/api/clients/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
