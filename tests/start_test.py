import pytest
import httpx
from httpx import AsyncClient, ASGITransport
from app.main import app  # Your FastAPI app

@pytest.mark.asyncio
async def test_login_for_access_token():
    form_data = {
        "username": "admin",
        "password": "secret"
    }
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/token", data=form_data)
        assert response.status_code == 200
        json_data = response.json()
        assert "access_token" in json_data
        assert json_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_create_qr_code_unauthorized():
    qr_request = {
        "url": "https://example.com",
        "fill_color": "red",
        "back_color": "white",
        "size": 10,
    }

    # Pass the FastAPI app to ASGITransport, not directly to AsyncClient
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/qr-codes/", json=qr_request)
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_and_delete_qr_code():
    form_data = {
        "username": "admin",
        "password": "secret",
    }

    # Create an ASGITransport using your FastAPI app.
    transport = ASGITransport(app=app)

    # Use the ASGI transport with AsyncClient (do not pass app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login and get the access token
        token_response = await ac.post("/token", data=form_data)
        assert token_response.status_code == 200, f"Login failed with status code {token_response.status_code}"
        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create a QR code
        qr_request = {
            "url": "https://example.com",
            "fill_color": "red",
            "back_color": "white",
            "size": 10,
        }
        create_response = await ac.post("/qr-codes/", json=qr_request, headers=headers)
        # Accept 200 (if your endpoint returns 200), 201, or 409
        assert create_response.status_code in [200, 201, 409], (
            f"Unexpected status code: {create_response.status_code}. "
            "Expected one of [200, 201, 409]."
        )

        # If the QR code was created (201), attempt to delete it
        if create_response.status_code == 201:
            qr_code_url = create_response.json()["qr_code_url"]
            qr_filename = qr_code_url.split("/")[-1]
            delete_response = await ac.delete(f"/qr-codes/{qr_filename}", headers=headers)
            assert delete_response.status_code == 204, (
                f"Delete failed with status code {delete_response.status_code}"
            )