import json
import logging

from openai import AsyncOpenAI

from app.config import AI_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

_openai_client: AsyncOpenAI | None = None
_anthropic_client = None  # AsyncAnthropic | None, imported lazily

EXTRACTION_PROMPT = """You are a resume/CV parser. Extract structured data from the following resume text.

Return a valid JSON object with this exact structure (use null for missing fields):
{
  "contact": {
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "+1234567890",
    "location": "City, Country",
    "linkedin": "linkedin.com/in/...",
    "github": "github.com/...",
    "website": "https://..."
  },
  "summary": "Professional summary or objective",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "start_date": "YYYY-MM or Month YYYY",
      "end_date": "YYYY-MM or Present",
      "description": "Key responsibilities and achievements"
    }
  ],
  "education": [
    {
      "institution": "University Name",
      "degree": "Bachelor's/Master's/PhD",
      "field": "Field of Study",
      "start_date": "YYYY",
      "end_date": "YYYY",
      "gpa": "3.8/4.0"
    }
  ],
  "certifications": [
    {
      "name": "Certification Name",
      "issuer": "Issuing Organization",
      "date": "YYYY-MM"
    }
  ],
  "languages": [
    {
      "name": "English",
      "proficiency": "Native/Fluent/Intermediate/Basic"
    }
  ]
}

IMPORTANT: Return ONLY the JSON object. No markdown, no explanation, no extra text.

Resume text:
"""


def init_ai_clients():
    global _openai_client, _anthropic_client
    if OPENAI_API_KEY:
        _openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized")
    if ANTHROPIC_API_KEY:
        from anthropic import AsyncAnthropic
        _anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Anthropic client initialized")
    if not _openai_client and not _anthropic_client:
        logger.error("No AI provider configured! Set OPENAI_API_KEY or ANTHROPIC_API_KEY")


async def extract_with_openai(text: str) -> tuple[dict, int]:
    response = await _openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a precise resume parser. Return only valid JSON."},
            {"role": "user", "content": EXTRACTION_PROMPT + text},
        ],
        temperature=0.1,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    tokens = response.usage.total_tokens if response.usage else 0
    logger.info(f"OpenAI extraction: {tokens} tokens used")
    return json.loads(content), tokens


async def extract_with_anthropic(text: str) -> tuple[dict, int]:
    response = await _anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": EXTRACTION_PROMPT + text},
        ],
        temperature=0.1,
    )
    content = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens
    logger.info(f"Anthropic extraction: {tokens} tokens used")

    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])

    return json.loads(content), tokens


async def extract_resume_data(text: str) -> tuple[dict, int]:
    primary = AI_PROVIDER

    # Try primary provider
    try:
        if primary == "anthropic" and _anthropic_client:
            return await extract_with_anthropic(text)
        elif _openai_client:
            return await extract_with_openai(text)
    except Exception as e:
        logger.warning(f"Primary provider ({primary}) failed: {e}")

    # Fallback to the other provider
    try:
        if primary == "openai" and _anthropic_client:
            logger.info("Falling back to Anthropic")
            return await extract_with_anthropic(text)
        elif primary == "anthropic" and _openai_client:
            logger.info("Falling back to OpenAI")
            return await extract_with_openai(text)
    except Exception as e:
        logger.error(f"Fallback provider also failed: {e}")

    raise RuntimeError("All AI providers failed")
