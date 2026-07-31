from typing import Literal

from pydantic import BaseModel, Field


VerificationStatus = Literal["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]


class VerificationResult(BaseModel):
    status: VerificationStatus
    confidence: float = Field(..., ge=0, le=1)
    reason: str
