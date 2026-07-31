# Installation Guide

## Prerequisites

- Docker Desktop
- Docker Compose
- Git

## Setup

```bash
cp .env.example .env
docker compose up --build
```

Set `GEMINI_API_KEY` and `TAVILY_API_KEY` in `.env` before calling `POST /api/analyze`.

Open:

- Frontend: `http://localhost:5173`
- Backend health endpoint: `http://localhost:8000/api/health`

## Manual Checks

1. Confirm the frontend loads with the HalluciScanAI page.
2. Confirm the API status badge shows `API online`.
3. Visit `http://localhost:8000/api/health` and confirm the JSON response contains `"status": "ok"`.
4. Send a `POST /api/analyze` request with factual text and confirm claims include status, confidence, reason, and evidence.
