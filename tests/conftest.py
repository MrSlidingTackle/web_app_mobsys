import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def authed_client(client):
    """Test client with a 'token' cookie set, so loginRequired passes."""
    client.set_cookie("token", "test-uid")
    return client
