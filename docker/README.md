# Docker Notes

Milestone 1 uses Docker Compose for local development.

- Backend: `http://localhost:8000`
- Backend health check: `http://localhost:8000/api/health`
- Frontend: `http://localhost:5173`

Copy `.env.example` to `.env` before running Compose.
Set `GEMINI_API_KEY` and `TAVILY_API_KEY` in `.env` for the backend analysis pipeline.
