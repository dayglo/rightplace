"""
Request context middleware for Prison Roll Call API.

Extracts user/officer ID from request for audit logging.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add user context to request state."""

    async def dispatch(self, request: Request, call_next):
        """
        Extract user ID from request and add to request.state.

        For MVP: Extract from X-Officer-ID header (stubbed auth)
        For production: Extract from JWT token after real auth is implemented
        """
        # MVP: Use header (stub authentication)
        request.state.user_id = request.headers.get("X-Officer-ID", "unknown")

        # Also store IP and user agent for audit logging
        request.state.client_ip = request.client.host if request.client else "unknown"
        request.state.user_agent = request.headers.get("user-agent", "")

        response = await call_next(request)
        return response
