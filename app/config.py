import os
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

TIER_LIMITS = {
    "free": 50,
    "pro": 1000,
    "ultra": 10000,
    "mega": 100000,
}

_raw_keys = os.getenv("API_KEYS", "demo-key-123:free")
API_KEYS: dict[str, str] = {}
for entry in _raw_keys.split(","):
    entry = entry.strip()
    if ":" in entry:
        key, tier = entry.rsplit(":", 1)
        API_KEYS[key.strip()] = tier.strip()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
