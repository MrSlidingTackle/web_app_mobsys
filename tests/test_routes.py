import pytest
from unittest.mock import patch, MagicMock

_GET = "app.routes.requests.get"

def mock_response(data):
    """Return a MagicMock that behaves like a requests.Response with .json()."""
    m = MagicMock()
    m.json.return_value = data
    return m

class TestIndex:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_renders_login_form(self, client):
        response = client.get("/")
        assert b"email" in response.data.lower()
        assert b"password" in response.data.lower()

class TestLoginRequired:
    @pytest.mark.parametrize("url", [
        "/home",
        "/new",
        "/details/5",
        "/protocol/1",
        "/contact",
    ])
    def test_redirect_to_index_without_token(self, client, url):
        response = client.get(url)
        assert response.status_code == 302
        assert response.location.endswith("/")

    @pytest.mark.parametrize("url", [
        "/home",
        "/new",
        "/details/55",
        "/protocol/1",
        "/contact",
    ])
    def test_no_redirect_with_token(self, authed_client, url):
        """With a valid token cookie, all protected routes should NOT return 302
        (status 200 is verified in the dedicated test classes below)."""

        def _stub(req_url, *args, **kwargs):
            return mock_response({
                "appointments": [],
                "appointment_types": [],
                "contacts": [],
                "products": [],
                "participants": [],
                "orders": [],
                "order_items": [],
                "protocols": [],
            })

        with patch(_GET, side_effect=_stub):
            response = authed_client.get(url)
        assert response.status_code != 302

class TestHome:
    def _appointments(self):
        return [
            {"id": 1, "uid": "test-uid",  "title": "My Termin",    "ort": "Berlin", "start": "2026-01-01 10:00", "ende": "2026-01-01 11:00"},
            {"id": 2, "uid": "other-uid", "title": "Other Termin", "ort": "Munich", "start": "2026-01-02 10:00", "ende": "2026-01-02 11:00"},
        ]

    def test_returns_200(self, authed_client):
        with patch(_GET, return_value=mock_response({"appointments": self._appointments()})):
            response = authed_client.get("/home")
        assert response.status_code == 200

    def test_shows_only_own_appointments(self, authed_client):
        """Only appointments whose uid matches the token cookie are rendered."""
        with patch(_GET, return_value=mock_response({"appointments": self._appointments()})):
            response = authed_client.get("/home")
        assert b"My Termin" in response.data
        assert b"Other Termin" not in response.data

    def test_empty_appointment_list(self, authed_client):
        with patch(_GET, return_value=mock_response({"appointments": []})):
            response = authed_client.get("/home")
        assert response.status_code == 200

class TestNew:
    def _side_effect(self, url, *args, **kwargs):
        if "terminart" in url:
            return mock_response({"appointment_types": [{"id": 1, "name": "Beratung"}]})
        if "kontakt" in url:
            return mock_response({"contacts": [{"id": 1, "ref_typ": "Kunde", "referenz_data": {"name": "Max Muster"}}]})
        if "products" in url:
            return mock_response({"products": [{"id": 1, "name": "Produkt A", "price": 9.99}]})
        return mock_response({})

    def test_returns_200(self, authed_client):
        with patch(_GET, side_effect=self._side_effect):
            response = authed_client.get("/new")
        assert response.status_code == 200

    def test_renders_appointment_types(self, authed_client):
        with patch(_GET, side_effect=self._side_effect):
            response = authed_client.get("/new")
        assert b"Beratung" in response.data

    def test_renders_contacts(self, authed_client):
        with patch(_GET, side_effect=self._side_effect):
            response = authed_client.get("/new")
        assert b"Max Muster" in response.data

    def test_renders_products(self, authed_client):
        with patch(_GET, side_effect=self._side_effect):
            response = authed_client.get("/new")
        assert b"Produkt A" in response.data

class TestDetails:
    def _side_effect(self, url, *args, **kwargs):
        if "/api/termine/" in url:
            return mock_response({
                "id": 1, "title": "Test Termin", "ort": "Berlin",
                "start": "2026-01-01 10:00", "ende": "2026-01-01 11:00",
                "art_id": 1, "uid": "test-uid",
            })
        if "terminart" in url:
            return mock_response({"appointment_types": [{"id": 1, "name": "Beratung"}]})
        if "kontakt" in url:
            return mock_response({"contacts": [{"id": 10, "ref_typ": "Kunde", "referenz_data": {"name": "Max Muster"}}]})
        if "teilnehmer" in url:
            return mock_response({"participants": [{"id": 1, "termin_id": 1, "kontakt_id": 10}]})
        if "products" in url:
            return mock_response({"products": [{"id": 5, "name": "Produkt A", "price": 9.99}]})
        if "auftragsposition" in url:
            return mock_response({"order_items": [{"id": 1, "auftrag_id": 99, "produkt_id": 5, "menge": 2}]})
        if "auftrag" in url:
            return mock_response({"orders": [{"id": 99, "termin_id": 1}]})
        return mock_response({})

    def test_returns_200(self, authed_client):
        with patch(_GET, side_effect=self._side_effect):
            response = authed_client.get("/details/55")
        assert response.status_code == 200

    def test_renders_termin_title(self, authed_client):
        with patch(_GET, side_effect=self._side_effect):
            response = authed_client.get("/details/55")
        assert b"Test Termin" in response.data

    def test_participant_name_resolved(self, authed_client):
        """The route joins teilnehmer with kontakte to attach a name."""
        with patch(_GET, side_effect=self._side_effect):
            response = authed_client.get("/details/55")
        assert b"Max Muster" in response.data

class TestProtocol:
    def _protocols(self):
        return [
            {"id": 1, "termin_id": 1, "content": "Protokoll Inhalt"},
            {"id": 2, "termin_id": 99, "content": "Anderes Protokoll"},
        ]

    def test_returns_200(self, authed_client):
        with patch(_GET, return_value=mock_response({"protocols": self._protocols()})):
            response = authed_client.get("/protocol/1")
        assert response.status_code == 200

    def test_no_matching_protocol_still_renders(self, authed_client):
        """When no protocol matches the termin_id the page still loads (protokoll
        defaults to empty string in the route)."""
        protocols = [{"id": 2, "termin_id": 99, "content": "Anderes Protokoll"}]
        with patch(_GET, return_value=mock_response({"protocols": protocols})):
            response = authed_client.get("/protocol/1")
        assert response.status_code == 200

    def test_empty_protocol_list(self, authed_client):
        with patch(_GET, return_value=mock_response({"protocols": []})):
            response = authed_client.get("/protocol/1")
        assert response.status_code == 200

class TestContact:
    def test_returns_200(self, authed_client):
        response = authed_client.get("/contact")
        assert response.status_code == 200
