# API Documentation

## Health Check

`GET /api/health`

Response:

```json
{
  "status": "ok",
  "service": "VeritasAI API",
  "version": "0.1.0"
}
```

## Analyze

`POST /api/analyze`

Request:

```json
{
  "text": "The AI generated response..."
}
```

Response:

```json
{
  "request_id": "4b7c3f44-5a7a-40ff-94ca-75ad34d2f63b",
  "processing_time_ms": 1234,
  "claims": [
    {
      "text": "Python was created by Guido van Rossum",
      "status": "SUPPORTED",
      "confidence": 0.91,
      "reason": "Multiple reliable sources confirm the claim.",
      "evidence": [
        {
          "title": "History of Python",
          "url": "https://www.python.org/doc/essays/blurb/",
          "content": "Python was created in the early 1990s by Guido van Rossum..."
        }
      ]
    }
  ]
}
```

Milestone 4 runs the backend pipeline: Gemini claim extraction, Tavily retrieval, CrossEncoder reranking, and Gemini verification.
