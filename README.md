# HalluciScan 🛡️

> **AI Hallucination Detection & Explainable Fact Verification**

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
## 📸 Screenshots

<h3>🏠 Landing Page</h3>

<p align="center">
  <img src="https://github.com/user-attachments/assets/3108e9e8-33df-4719-a2de-64b9d208e9bb" width="900">
</p>

<h3>⚡ Analysis in Progress</h3>

<p align="center">
  <img src="https://github.com/user-attachments/assets/6bf04722-b207-45a9-a051-37a3a7ade98b" width="900">
</p>

<h3>✅ Results Dashboard</h3>

<p align="center">
 <img width="1903" height="950" alt="image" src="https://github.com/user-attachments/assets/2bc5b329-7e40-40af-9b55-e1b125799672" />

  <img src="https://github.com/user-attachments/assets/61f49658-85dc-48ee-8f06-afc5f028ec28" width="48%">
</p>
---

