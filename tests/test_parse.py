import pytest


@pytest.mark.asyncio
async def test_parse_text_success(client, api_headers):
    response = await client.post(
        "/parse/text",
        params={"text": "John Doe, Software Engineer, Python, 5 years experience"},
        headers=api_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is not None
    assert data["data"]["contact"]["name"] == "John Doe"


@pytest.mark.asyncio
async def test_parse_text_empty(client, api_headers):
    response = await client.post(
        "/parse/text",
        params={"text": "   "},
        headers=api_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_parse_file_unsupported_type(client, api_headers):
    response = await client.post(
        "/parse",
        headers=api_headers,
        files={"file": ("test.jpg", b"fake image data", "image/jpeg")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_parse_file_empty(client, api_headers):
    response = await client.post(
        "/parse",
        headers=api_headers,
        files={"file": ("test.txt", b"", "text/plain")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_parse_file_txt_success(client, api_headers):
    response = await client.post(
        "/parse",
        headers=api_headers,
        files={"file": ("resume.txt", b"John Doe, Python Developer", "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
