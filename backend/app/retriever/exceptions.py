class RetrievalError(Exception):
    pass


class RetrievalConfigError(RetrievalError):
    pass


class RetrievalRateLimitError(RetrievalError):
    pass


class RetrievalTimeoutError(RetrievalError):
    pass
