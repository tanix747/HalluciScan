import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.analyze_service import (
    AnalyzeDependencyConfigError,
    AnalyzeProcessingError,
    AnalyzeRateLimitError,
    AnalyzeService,
    AnalyzeTimeoutError,
    AnalyzeValidationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])


def get_analyze_service() -> AnalyzeService:
    return AnalyzeService()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    service: AnalyzeService = Depends(get_analyze_service),
) -> AnalyzeResponse:
    try:
        return await service.analyze(request)
    except AnalyzeValidationError as exc:
        logger.warning("Analyze request failed validation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except AnalyzeRateLimitError as exc:
        logger.warning("Analyze request rate limited: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except AnalyzeTimeoutError as exc:
        logger.warning("Analyze request timed out: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except AnalyzeDependencyConfigError as exc:
        logger.error("Analyze dependency is not configured: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except AnalyzeProcessingError as exc:
        logger.warning("Analyze request failed during processing: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected analyze request failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis request failed",
        ) from exc
