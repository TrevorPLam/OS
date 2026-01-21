from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from modules.auth import saml_views


def _set_session_state(client: APIClient, relay_state: str) -> None:
    session = client.session
    session["saml_relay_state"] = relay_state
    session.save()


def _build_auth_class(attributes: dict, name_id: str, errors: list[str] | None = None):
    class DummyAuth:
        def __init__(self, req, settings):
            self._attributes = attributes
            self._name_id = name_id
            self._errors = errors or []

        def process_response(self) -> None:
            return None

        def get_errors(self) -> list[str]:
            return self._errors

        def get_last_error_reason(self) -> str:
            return "simulated error"

        def is_authenticated(self) -> bool:
            return True

        def get_attributes(self) -> dict:
            return self._attributes

        def get_nameid(self) -> str:
            return self._name_id

    return DummyAuth


class TestSAMLACSView(TestCase):
    def test_saml_acs_rejects_missing_relay_state(self):
        with mock.patch.object(saml_views, "SAML_AVAILABLE", True):
            client = APIClient()
            response = client.post("/api/v1/auth/saml/acs/", data={})

        assert response.status_code == 400
        assert b"Invalid SAML request: missing state" in response.content

    def test_saml_acs_rejects_state_mismatch(self):
        with mock.patch.object(saml_views, "SAML_AVAILABLE", True):
            client = APIClient()
            _set_session_state(client, "expected-state")

            response = client.post("/api/v1/auth/saml/acs/", data={"RelayState": "wrong"})

        assert response.status_code == 400
        assert b"Invalid SAML request: state mismatch" in response.content
        assert client.session.get("saml_relay_state") == "expected-state"

    def test_saml_acs_handles_missing_attributes(self):
        auth_class = _build_auth_class(attributes={}, name_id="user@example.com")
        with (
            mock.patch.object(saml_views, "SAML_AVAILABLE", True),
            mock.patch.object(saml_views, "get_saml_settings", return_value={"strict": True}),
            mock.patch.object(saml_views, "OneLogin_Saml2_Auth", auth_class),
        ):
            client = APIClient()
            _set_session_state(client, "relay-state")

            response = client.post("/api/v1/auth/saml/acs/", data={"RelayState": "relay-state"})

        user = get_user_model().objects.get(email="user@example.com")
        assert response.status_code == 200
        assert user.first_name == ""
        assert user.last_name == ""
        assert "saml_relay_state" not in client.session

    def test_saml_acs_returns_generic_error_on_auth_failure(self):
        auth_class = _build_auth_class(attributes={}, name_id="user@example.com", errors=["error"])
        with (
            mock.patch.object(saml_views, "SAML_AVAILABLE", True),
            mock.patch.object(saml_views, "get_saml_settings", return_value={"strict": True}),
            mock.patch.object(saml_views, "OneLogin_Saml2_Auth", auth_class),
        ):
            client = APIClient()
            _set_session_state(client, "relay-state")

            response = client.post("/api/v1/auth/saml/acs/", data={"RelayState": "relay-state"})

        assert response.status_code == 400
        assert b"SAML authentication failed" in response.content


class TestSAMLAttributeExtraction(TestCase):
    def test_extract_saml_user_attributes_happy(self):
        # Happy path: IdP provides all expected attributes.
        attributes = {
            "email": ["user@example.com"],
            "first_name": ["Ada"],
            "last_name": ["Lovelace"],
        }

        email, first_name, last_name, missing_fields = saml_views._extract_saml_user_attributes(
            attributes,
            name_id="user@example.com",
        )

        assert email == "user@example.com"
        assert first_name == "Ada"
        assert last_name == "Lovelace"
        assert missing_fields == []

    def test_extract_saml_user_attributes_empty(self):
        # Edge case: attributes empty, so we rely on NameID fallback.
        attributes = {}

        email, first_name, last_name, missing_fields = saml_views._extract_saml_user_attributes(
            attributes,
            name_id="fallback@example.com",
        )

        assert email == "fallback@example.com"
        assert first_name == ""
        assert last_name == ""
        assert sorted(missing_fields) == ["email", "first_name", "last_name"]

    def test_extract_saml_user_attributes_error(self):
        # Error path: no email attribute and no NameID should raise.
        attributes = {}

        with self.assertRaises(ValueError):
            saml_views._extract_saml_user_attributes(attributes, name_id=None)
