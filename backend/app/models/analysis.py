from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="AI-generated response text to analyze.",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class Evidence(BaseModel):
    title: str
    url: str
    content: str


class Claim(BaseModel):
    text: str
    status: Literal["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"] | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reason: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    request_id: str
    processing_time_ms: int
    claims: list[Claim] = Field(default_factory=list)
