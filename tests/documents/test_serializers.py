"""
Tests for Documents module serializers.
"""
import pytest
from django.contrib.auth.models import User
from modules.crm.models import Client
from modules.documents.models import Folder, Document
from api.documents.serializers import FolderSerializer, DocumentSerializer


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(username='testuser', password='testpass123')


@pytest.fixture
def client_obj(db, user):
    """Create test client."""
    return Client.objects.create(
        company_name='Test Company',
        primary_contact_name='John Doe',
        primary_contact_email='john@test.com',
        owner=user,
        status='active'
    )


@pytest.fixture
def folder(db, client_obj, user):
    """Create test folder."""
    return Folder.objects.create(
        client=client_obj,
        name='Test Folder',
        visibility='internal',
        created_by=user
    )


@pytest.mark.unit
@pytest.mark.django_db
class TestFolderSerializer:
    """Test FolderSerializer."""

    def test_valid_folder_data(self, client_obj, user):
        """Test serializer accepts valid folder data."""
        data = {
            'client': client_obj.id,
            'name': 'Test Folder',
            'description': 'A test folder',
            'visibility': 'internal',
            'created_by': user.id
        }
        serializer = FolderSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_folder_hierarchy(self, client_obj, folder, user):
        """Test nested folder creation."""
        data = {
            'client': client_obj.id,
            'parent': folder.id,
            'name': 'Subfolder',
            'visibility': 'internal',
            'created_by': user.id
        }
        serializer = FolderSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        subfolder = serializer.save()
        assert subfolder.parent == folder

    def test_client_name_read_only(self, folder):
        """Test client_name is read-only field."""
        serializer = FolderSerializer(folder)
        assert 'client_name' in serializer.data
        assert serializer.data['client_name'] == folder.client.company_name


@pytest.mark.unit
@pytest.mark.django_db
class TestDocumentSerializer:
    """Test DocumentSerializer."""

    def test_valid_document_data(self, client_obj, folder, user):
        """Test serializer accepts valid document data."""
        data = {
            'folder': folder.id,
            'client': client_obj.id,
            'name': 'Test Document.pdf',
            'visibility': 'internal',
            'file_type': 'application/pdf',
            'file_size_bytes': 1024,
            's3_key': 'client-1/documents/test.pdf',
            's3_bucket': 'consultantpro-docs',
            'uploaded_by': user.id
        }
        serializer = DocumentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_document_metadata_fields(self, client_obj, folder, user):
        """Test document includes all metadata fields."""
        document = Document.objects.create(
            folder=folder,
            client=client_obj,
            name='Test.pdf',
            file_type='application/pdf',
            file_size_bytes=2048,
            s3_key='test-key',
            s3_bucket='test-bucket',
            uploaded_by=user
        )
        serializer = DocumentSerializer(document)
        assert serializer.data['file_size_bytes'] == 2048
        assert serializer.data['current_version'] == 1
        assert 'folder_name' in serializer.data
        assert 'client_name' in serializer.data


@pytest.mark.integration
@pytest.mark.django_db
class TestDocumentWorkflow:
    """Test document management workflow."""

    def test_document_visibility_change(self, client_obj, folder, user):
        """Test changing document visibility."""
        document = Document.objects.create(
            folder=folder,
            client=client_obj,
            name='Secret.pdf',
            file_type='application/pdf',
            file_size_bytes=1024,
            s3_key='secret-key',
            s3_bucket='test-bucket',
            visibility='internal',
            uploaded_by=user
        )

        # Change to client-visible
        data = {'visibility': 'client'}
        serializer = DocumentSerializer(document, data=data, partial=True)
        assert serializer.is_valid()
        updated_doc = serializer.save()
        assert updated_doc.visibility == 'client'
