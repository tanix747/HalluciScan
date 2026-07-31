# HalluciScan 🛡️

> **Evidence-backed AI Hallucination Detection using RAG and Semantic Reranking**

HalluciScan detects factual hallucinations in AI-generated or human-written text by extracting claims, retrieving live evidence from the web, reranking relevant sources, and generating explainable verdicts with confidence scores.

---

## Features

- AI-powered claim extraction
- Live web evidence retrieval
- Semantic reranking using CrossEncoder
- Explainable claim verification
- Confidence score for every claim
- Source-backed evidence
- Modern React frontend
- FastAPI backend

---

## Tech Stack

### Frontend
- React
- TypeScript
- Vite

### Backend
- FastAPI
- Python

### AI
- Gemini 3.6 Flash
- Tavily Search API
- CrossEncoder (MS MARCO MiniLM)

---

## Architecture

```
User Input
     │
     ▼
Claim Extraction (Gemini)
     │
     ▼
Evidence Retrieval (Tavily)
     │
     ▼
Semantic Reranking (CrossEncoder)
     │
     ▼
Claim Verification (Gemini)
     │
     ▼
Explainable Verdicts
```

---

## Running Locally

### Backend

```bash
python -m venv .venv
pip install -r backend/requirements.txt

uvicorn app.main:app --reload --app-dir backend
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=
TAVILY_API_KEY=
GEMINI_MODEL=gemini-3.6-flash
```

---

