import pytest
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, ASGITransport
from fakeredis.aioredis import FakeRedis


MOCK_PARSED_DATA = {
    "contact": {"name": "John Doe", "email": "john@example.com"},
    "summary": "Experienced developer",
    "skills": ["Python", "FastAPI"],
    "experience": [],
    "education": [],
    "certifications": [],
    "languages": [],
}


@pytest.fixture
async def fake_redis():
    r = FakeRedis(decode_responses=True)
    yield r
    await r.flushall()
    await r.close()


@pytest.fixture
async def client(fake_redis):
    with patch("app.middleware.auth._redis", fake_redis):
        mock_extract = AsyncMock(return_value=(MOCK_PARSED_DATA, 500))
        with patch("app.services.ai_extractor.extract_resume_data", mock_extract):
            with patch("app.services.ai_extractor.init_ai_clients"):
                from app.main import app
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as ac:
                    yield ac


@pytest.fixture
def api_headers():
    return {"X-API-Key": "demo-key-123"}
