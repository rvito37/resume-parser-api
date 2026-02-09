from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import ParseResponse, ParsedResume, HealthResponse, UsageResponse
from app.services.document_parser import extract_text
from app.services.ai_extractor import extract_resume_data
from app.middleware.auth import get_api_key, check_rate_limit
from app.config import MAX_FILE_SIZE, ALLOWED_CONTENT_TYPES

app = FastAPI(
    title="Resume Parser API",
    description="AI-powered resume/CV parser. Upload a PDF, DOCX, or TXT file and get structured JSON data.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/usage", response_model=UsageResponse)
async def get_usage(api_key: str = Depends(get_api_key)):
    usage = check_rate_limit(api_key)
    # Decrement since check_rate_limit increments
    # We just want to check, not consume
    import json, os
    from app.middleware.auth import USAGE_FILE, _load_usage, _save_usage, _get_month_key
    data = _load_usage()
    month_key = _get_month_key()
    if api_key in data and month_key in data[api_key]:
        data[api_key][month_key] -= 1
        _save_usage(data)
        usage["requests_used"] -= 1
    return UsageResponse(**usage)


@app.post("/parse", response_model=ParseResponse)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    api_key: str = Depends(get_api_key),
):
    # Check rate limit
    usage_info = check_rate_limit(api_key)

    # Validate content type
    content_type = file.content_type
    if content_type not in ALLOWED_CONTENT_TYPES:
        # Try to detect by extension
        filename = file.filename or ""
        if filename.endswith(".pdf"):
            content_type = "application/pdf"
        elif filename.endswith(".docx"):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename.endswith(".txt"):
            content_type = "text/plain"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {content_type}. Accepted: PDF, DOCX, TXT",
            )

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Extract text
    try:
        raw_text = extract_text(file_bytes, content_type)
    except Exception as e:
        return ParseResponse(success=False, error=f"Failed to extract text: {str(e)}")

    if not raw_text.strip():
        return ParseResponse(success=False, error="No text could be extracted from the file.")

    # Truncate very long resumes to save tokens
    if len(raw_text) > 15000:
        raw_text = raw_text[:15000]

    # AI extraction
    try:
        parsed_data, tokens_used = await extract_resume_data(raw_text)
    except Exception as e:
        return ParseResponse(success=False, error=f"AI extraction failed: {str(e)}")

    # Build response
    try:
        resume = ParsedResume(**parsed_data, raw_text=raw_text[:2000])
    except Exception:
        # If validation fails, try to return what we can
        resume = ParsedResume(raw_text=raw_text[:2000])
        for key, value in parsed_data.items():
            if hasattr(resume, key):
                try:
                    setattr(resume, key, value)
                except Exception:
                    pass

    return ParseResponse(success=True, data=resume, tokens_used=tokens_used)


@app.post("/parse/text", response_model=ParseResponse)
async def parse_resume_text(
    text: str,
    api_key: str = Depends(get_api_key),
):
    """Parse resume from plain text (no file upload needed)."""
    usage_info = check_rate_limit(api_key)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text.")

    if len(text) > 15000:
        text = text[:15000]

    try:
        parsed_data, tokens_used = await extract_resume_data(text)
    except Exception as e:
        return ParseResponse(success=False, error=f"AI extraction failed: {str(e)}")

    try:
        resume = ParsedResume(**parsed_data, raw_text=text[:2000])
    except Exception:
        resume = ParsedResume(raw_text=text[:2000])

    return ParseResponse(success=True, data=resume, tokens_used=tokens_used)
