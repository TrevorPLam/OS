import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from api.documents.serializers import DocumentSerializer
from modules.clients.models import Client
from modules.documents.models import Document, Folder, Version
from modules.firm.models import BreakGlassSession, Firm, PlatformUserProfile


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username='firm-user', password='test-pass')


@pytest.fixture
def firm(db):
    return Firm.objects.create(name='Crypto Firm', slug='crypto-firm', kms_key_id='test-key')


@pytest.fixture
def client_obj(db, firm, user):
    return Client.objects.create(
        company_name='Crypto Client',
        primary_contact_name='Contact Name',
        primary_contact_email='contact@example.com',
        firm=firm,
        client_since=timezone.now().date(),
        account_manager=user,
        status='active',
    )


@pytest.fixture
def folder(db, firm, client_obj, user):
    return Folder.objects.create(
        firm=firm,
        client=client_obj,
        name='Encrypted Folder',
        visibility='internal',
        created_by=user,
    )


@pytest.fixture
def platform_user(db):
    operator = get_user_model().objects.create_user(username='platform-operator', password='test-pass')
    PlatformUserProfile.objects.create(
        user=operator,
        platform_role=PlatformUserProfile.ROLE_PLATFORM_OPERATOR,
        is_platform_active=True,
        can_activate_break_glass=True,
    )
    return operator


def _build_request(user, firm):
    request = APIRequestFactory().get('/')
    request.user = user
    request.firm = firm
    return request


@pytest.mark.unit
@pytest.mark.django_db
def test_document_encryption_round_trip(firm, client_obj, folder, user):
    document = Document.objects.create(
        firm=firm,
        folder=folder,
        client=client_obj,
        name='Secret.pdf',
        file_type='application/pdf',
        file_size_bytes=256,
        s3_key='firm-1/client-1/secret.pdf',
        s3_bucket='private-bucket',
        uploaded_by=user,
    )

    assert document.s3_key.startswith('enc::')
    assert document.s3_bucket.startswith('enc::')
    assert document.s3_fingerprint != ''
    assert document.decrypted_s3_key() == 'firm-1/client-1/secret.pdf'
    assert document.decrypted_s3_bucket() == 'private-bucket'

    version = Version.objects.create(
        firm=firm,
        document=document,
        version_number=1,
        change_summary='Initial upload',
        file_type='application/pdf',
        file_size_bytes=256,
        s3_key='firm-1/client-1/secret.pdf',
        s3_bucket='private-bucket',
        uploaded_by=user,
    )

    assert version.s3_key.startswith('enc::')
    assert version.s3_bucket.startswith('enc::')
    assert version.decrypted_s3_key() == 'firm-1/client-1/secret.pdf'
    assert version.decrypted_s3_bucket() == 'private-bucket'


@pytest.mark.unit
@pytest.mark.django_db
def test_s3_fingerprint_uniqueness(firm, client_obj, folder, user):
    Document.objects.create(
        firm=firm,
        folder=folder,
        client=client_obj,
        name='First.pdf',
        file_type='application/pdf',
        file_size_bytes=100,
        s3_key='duplicate-key',
        s3_bucket='same-bucket',
        uploaded_by=user,
    )

    with pytest.raises(IntegrityError):
        Document.objects.create(
            firm=firm,
            folder=folder,
            client=client_obj,
            name='Second.pdf',
            file_type='application/pdf',
            file_size_bytes=120,
            s3_key='duplicate-key',
            s3_bucket='same-bucket',
            uploaded_by=user,
        )


@pytest.mark.unit
@pytest.mark.django_db
def test_serializer_hides_content_without_break_glass(firm, client_obj, folder, user, platform_user):
    document = Document.objects.create(
        firm=firm,
        folder=folder,
        client=client_obj,
        name='Hidden.pdf',
        file_type='application/pdf',
        file_size_bytes=100,
        s3_key='hidden-key',
        s3_bucket='hidden-bucket',
        uploaded_by=user,
    )

    request = _build_request(platform_user, firm)
    serializer = DocumentSerializer(document, context={'request': request})
    assert 's3_key' not in serializer.data
    assert 's3_bucket' not in serializer.data


@pytest.mark.unit
@pytest.mark.django_db
def test_serializer_exposes_content_with_break_glass(firm, client_obj, folder, user, platform_user):
    document = Document.objects.create(
        firm=firm,
        folder=folder,
        client=client_obj,
        name='Visible.pdf',
        file_type='application/pdf',
        file_size_bytes=100,
        s3_key='visible-key',
        s3_bucket='visible-bucket',
        uploaded_by=user,
    )

    BreakGlassSession.objects.create(
        firm=firm,
        operator=platform_user,
        reason='Support incident',
        expires_at=timezone.now() + timezone.timedelta(hours=1),
    )

    request = _build_request(platform_user, firm)
    serializer = DocumentSerializer(document, context={'request': request})
    assert serializer.data['s3_key'] == 'visible-key'
    assert serializer.data['s3_bucket'] == 'visible-bucket'
