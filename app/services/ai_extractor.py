import json
from app.config import AI_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY

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


async def extract_with_openai(text: str) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
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
    return json.loads(content), tokens


async def extract_with_anthropic(text: str) -> dict:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": EXTRACTION_PROMPT + text},
        ],
        temperature=0.1,
    )
    content = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens

    # Clean up potential markdown wrapping
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])

    return json.loads(content), tokens


async def extract_resume_data(text: str) -> tuple[dict, int]:
    if AI_PROVIDER == "anthropic":
        return await extract_with_anthropic(text)
    else:
        return await extract_with_openai(text)
