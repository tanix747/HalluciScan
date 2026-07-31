# Folder Explanation

```text
backend/
  app/
    api/              FastAPI route modules
    claim_extractor/  Gemini-backed factual claim extraction
    core/             Configuration and app-level wiring
    database/         Future persistence adapters
    models/           Pydantic response and domain models
    reranker/         CrossEncoder evidence reranking
    retriever/        Tavily evidence retrieval
    services/         Backend orchestration services
    utils/            Shared backend utilities
    verifier/         Gemini-backed claim verification
  tests/              Backend unit tests

frontend/
  src/                React application source

docs/                 Project documentation
docker/               Docker-specific notes and future deployment assets
```
