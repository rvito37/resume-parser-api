# Resume Parser API

AI-powered resume/CV parser. Upload PDF, DOCX, or TXT — get structured JSON.

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/rvito37/resume-parser-api.git
cd resume-parser-api
cp .env.example .env
```

Edit `.env` — add your OpenAI or Anthropic API key.

### 2. Run Locally

```bash
pip install -r requirements.txt
python run.py
```

API docs: http://localhost:8000/docs

### 3. Run with Docker

```bash
docker compose up -d
```

## API Endpoints

### `POST /parse`
Upload a resume file (PDF, DOCX, TXT).

```bash
curl -X POST http://localhost:8000/parse \
  -H "X-API-Key: demo-key-123" \
  -F "file=@resume.pdf"
```

### `POST /parse/text`
Send resume as plain text.

```bash
curl -X POST "http://localhost:8000/parse/text?text=John+Doe..." \
  -H "X-API-Key: demo-key-123"
```

### `GET /usage`
Check API usage for your key.

### Response Format

```json
{
  "success": true,
  "data": {
    "contact": { "name": "John Doe", "email": "john@example.com", ... },
    "summary": "Senior developer with 10 years...",
    "skills": ["Python", "FastAPI", "Docker"],
    "experience": [{ "company": "...", "title": "...", ... }],
    "education": [{ "institution": "...", "degree": "...", ... }],
    "certifications": [...],
    "languages": [...]
  },
  "tokens_used": 1250
}
```

## Pricing Tiers

| Tier | Requests/month | Price |
|------|---------------|-------|
| Free | 50 | $0 |
| Pro | 1,000 | $29 |
| Ultra | 10,000 | $99 |
| Mega | 100,000 | $249 |

## Deploy to VPS (5 steps)

### Step 1: Get a VPS
- Hetzner CX22 ($4.5/mo) or DigitalOcean ($6/mo)
- Ubuntu 22.04, install Docker

### Step 2: Deploy
```bash
ssh root@your-server
git clone https://github.com/rvito37/resume-parser-api.git
cd resume-parser-api
cp .env.example .env
nano .env  # add your API keys
docker compose up -d
```

### Step 3: Add HTTPS (optional but recommended)
```bash
apt install nginx certbot python3-certbot-nginx
# Configure nginx reverse proxy to port 8000
# Run certbot for free SSL
```

### Step 4: Publish on RapidAPI
1. Go to https://rapidapi.com/provider
2. Click "Add New API"
3. Set base URL: `https://your-domain.com`
4. Add endpoints: `/parse` (POST), `/parse/text` (POST), `/usage` (GET)
5. Set pricing tiers matching the table above
6. Add API description and examples

### Step 5: Add API keys for customers
Edit `.env` to add customer keys:
```
API_KEYS=demo-key-123:free,customer1-key:pro,customer2-key:ultra
```
Restart: `docker compose restart`

## Managing Customers

When a customer subscribes on RapidAPI, you'll get a webhook. Add their key to `.env` and restart. For production scale, replace the file-based auth with a database (Redis/PostgreSQL).
