class VerificationError(Exception):
    pass


class VerificationConfigError(VerificationError):
    pass


class VerificationParseError(VerificationError):
    pass


class VerificationRateLimitError(VerificationError):
    pass


class VerificationTimeoutError(VerificationError):
    pass
