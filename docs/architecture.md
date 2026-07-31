# Architecture

VeritasAI is organized as a modular full-stack system.

```mermaid
flowchart LR
    User["User"] --> Frontend["React + Vite Frontend"]
    Frontend --> API["FastAPI Backend"]
    API --> AnalyzeService["AnalyzeService Orchestrator"]
    AnalyzeService --> ClaimExtractor["ClaimExtractor Gemini"]
    AnalyzeService --> Retriever["Retriever Tavily"]
    AnalyzeService --> Reranker["Reranker CrossEncoder"]
    AnalyzeService --> Verifier["Verifier Gemini"]
    AnalyzeService -. later .-> Database["SQLite + FAISS Artifacts"]
```

Milestone 4 implements the complete core backend pipeline. Persistence, authentication, deployment hardening, and frontend result rendering are separate future milestones.
