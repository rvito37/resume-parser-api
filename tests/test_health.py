import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_returns_request_id(client):
    response = await client.get("/")
    assert "x-request-id" in response.headers
