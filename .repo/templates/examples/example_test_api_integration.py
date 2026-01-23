"""
Example: API Integration Test Pattern
File: tests/integration/test_client_api_flow.py
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
    """Create a test user."""
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
    """Create authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=user)
    client.force_authenticate(firm=firm)
    return client


@pytest.mark.django_db
class TestClientAPIFlow:
    """Integration tests for complete client API workflows."""

    def test_create_list_update_delete_flow(self, api_client, firm):
        """Test complete CRUD workflow."""
        # Create
        create_data = {'name': 'New Client', 'firm': firm.id}
        create_response = api_client.post('/api/clients/', create_data, format='json')
        assert create_response.status_code == status.HTTP_201_CREATED
        client_id = create_response.data['id']

        # List
        list_response = api_client.get('/api/clients/')
        assert list_response.status_code == status.HTTP_200_OK
        assert any(c['id'] == client_id for c in list_response.data['results'])

        # Retrieve
        get_response = api_client.get(f'/api/clients/{client_id}/')
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data['name'] == 'New Client'

        # Update
        update_data = {'name': 'Updated Client'}
        update_response = api_client.patch(
            f'/api/clients/{client_id}/', update_data, format='json'
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.data['name'] == 'Updated Client'

        # Delete
        delete_response = api_client.delete(f'/api/clients/{client_id}/')
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        get_response = api_client.get(f'/api/clients/{client_id}/')
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_pagination(self, api_client, firm):
        """Test API pagination."""
        # Create multiple clients
        for i in range(15):
            Client.objects.create(firm=firm, name=f'Client {i}')

        # First page
        response = api_client.get('/api/clients/?page=1')
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'count' in response.data
        assert response.data['count'] == 15

    def test_filtering(self, api_client, firm):
        """Test API filtering."""
        Client.objects.create(firm=firm, name='Active Client', status='active')
        Client.objects.create(firm=firm, name='Inactive Client', status='inactive')

        response = api_client.get('/api/clients/?status=active')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Active Client'
