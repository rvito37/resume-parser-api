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

### 2. Run with Docker (recommended)

```bash
docker compose up -d
```

This starts the API server + Redis for rate limiting.

API docs: http://localhost:8000/docs

### 3. Run Locally (development)

```bash
pip install -r requirements-dev.txt
python run.py
```

Requires Redis running locally on port 6379 (or set `REDIS_URL` in `.env`).

### 4. Run Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
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
    "contact": { "name": "John Doe", "email": "john@example.com", "..." : "..." },
    "summary": "Senior developer with 10 years...",
    "skills": ["Python", "FastAPI", "Docker"],
    "experience": [{ "company": "...", "title": "...", "..." : "..." }],
    "education": [{ "institution": "...", "degree": "...", "..." : "..." }],
    "certifications": ["..."],
    "languages": ["..."]
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

## Deploy to VPS

### Step 1: Get a VPS
- Hetzner CX22 ($4.5/mo) or DigitalOcean ($6/mo)
- Ubuntu 22.04

### Step 2: Server setup
```bash
apt update && apt install -y docker.io docker-compose-v2 nginx certbot python3-certbot-nginx
```

### Step 3: Deploy
```bash
ssh root@your-server
git clone https://github.com/rvito37/resume-parser-api.git
cd resume-parser-api
cp .env.example .env
nano .env  # set OPENAI_API_KEY, API_KEYS, ENVIRONMENT=production
docker compose up -d
```

### Step 4: Configure Nginx + SSL
```bash
cp nginx/nginx.conf /etc/nginx/sites-available/resume-parser
ln -s /etc/nginx/sites-available/resume-parser /etc/nginx/sites-enabled/
# Edit server_name in the config to your domain
nginx -t && systemctl reload nginx
certbot --nginx -d your-domain.com
```

### Step 5: Verify
```bash
curl https://your-domain.com/
# {"status":"ok","version":"1.0.0","environment":"production"}
```

### Step 6: Publish on RapidAPI
1. Go to https://rapidapi.com/provider
2. Click "Add New API"
3. Set base URL: `https://your-domain.com`
4. Add endpoints: `/parse` (POST), `/parse/text` (POST), `/usage` (GET)
5. Set pricing tiers matching the table above
6. Set `RAPIDAPI_PROXY_SECRET` in `.env` to the secret from RapidAPI dashboard

### Step 7: Add API keys for customers
Edit `.env` to add customer keys:
```
API_KEYS=demo-key-123:free,customer1-key:pro,customer2-key:ultra
```
Restart: `docker compose restart api`

## Architecture

```
FastAPI (async) → OpenAI gpt-4o-mini (primary) / Anthropic Claude (fallback)
Rate limiting → Redis (atomic INCR, auto-expiring keys)
Deployment → Docker Compose (API + Redis) behind Nginx
```

## Development

```bash
# Dev mode with hot reload + Redis
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Run tests (no Docker needed)
pip install -r requirements-dev.txt
pytest tests/ -v
```
