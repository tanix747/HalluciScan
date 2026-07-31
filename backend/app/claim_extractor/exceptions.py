class ClaimExtractionError(Exception):
    pass


class ClaimExtractionConfigError(ClaimExtractionError):
    pass


class ClaimExtractionParseError(ClaimExtractionError):
    pass


class ClaimExtractionRateLimitError(ClaimExtractionError):
    pass


class ClaimExtractionTimeoutError(ClaimExtractionError):
    pass
