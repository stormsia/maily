from __future__ import annotations


class MailAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data: dict = response_data or {}


class MailAuthError(MailAPIError):
    pass


class MailNotFoundError(MailAPIError):
    pass


class MailRateLimitError(MailAPIError):
    def __init__(self, message: str, retry_after: float | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class MailServerError(MailAPIError):
    pass


class MailTimeoutError(MailAPIError):
    pass


class MailConflictError(MailAPIError):
    pass


class MailValidationError(MailAPIError):
    pass
