"""
Error types for Discord API interactions
"""
from typing import Optional, List, Dict, Any


class DiscordError(Exception):
    """Base exception for Discord API errors"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class HTTPError(DiscordError):
    """Error for Discord HTTP API failures"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class GatewayError(DiscordError):
    """Error for Discord Gateway connection issues"""
    def __init__(self, code: int, message: str):
        self.code = code
        super().__init__(f"Gateway error {code}: {message}")


class RatelimitError(DiscordError):
    """Error for Discord API rate limiting"""
    def __init__(self, retry_after: float, message: Optional[str] = None):
        self.retry_after = retry_after
        msg = message or f"Rate limited, retry after {retry_after} seconds"
        super().__init__(msg)


class ValidationError(DiscordError):
    """Error for invalid API requests"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        msg = f"Validation error: {message}"
        if field:
            msg = f"Validation error in '{field}': {message}"
        super().__init__(msg)
