import pytest


@pytest.mark.asyncio
async def test_missing_api_key(client):
    response = await client.post("/parse/text", params={"text": "test resume"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_api_key(client):
    response = await client.post(
        "/parse/text",
        params={"text": "test resume"},
        headers={"X-API-Key": "bad-key-999"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_rate_limit_enforced(client, fake_redis, api_headers):
    # Set usage to the limit (free tier = 50)
    await fake_redis.set("usage:demo-key-123:2026-02", 50)
    response = await client.post(
        "/parse/text",
        params={"text": "test resume content"},
        headers=api_headers,
    )
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_usage_endpoint(client, api_headers):
    response = await client.get("/usage", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert "tier" in data
    assert "requests_used" in data
    assert "requests_limit" in data
