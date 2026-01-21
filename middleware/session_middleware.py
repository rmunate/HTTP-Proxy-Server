from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi.responses import JSONResponse
from services.sesion_manager import SessionManager
from services.log import Log

class SessionMiddleware(BaseHTTPMiddleware):
    """
    Implement session ID validation for incoming requests.

    Attributes
    ----------
    URI_EXCEPTIONS : list[str]
        List of URI paths excluded from session validation.
    """

    URI_EXCEPTIONS = [
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health-check",
        "/favicon.ico",
        "/subscribe",
    ]

    async def dispatch(
        self, request: Request, call_next: callable
    ) -> JSONResponse:
        """
        Validate session ID in request headers and process the request.

        Parameters
        ----------
        request : Request
            Incoming HTTP request object.
        call_next : callable
            Next middleware or route handler to call.

        Returns
        -------
        JSONResponse
            HTTP response after session validation.
        """
        try:

            # Skip session validation for specified URIs
            if str(request.url.path) in self.URI_EXCEPTIONS:
                Log.info(f"Bypassing session validation for URI: {request.url.path}")
                return await call_next(request)

            # Retrieve session ID from request headers
            session_id: str | None = request.headers.get("X-Session-Id")
            if not session_id:
                error_msg = "Session ID is missing. Please provide a valid session ID."
                Log.error(error_msg)
                return JSONResponse(
                    status_code=401,
                    content={"message": error_msg},
                )

            # Validate session ID using SessionManager
            manager: SessionManager = SessionManager()

            # Clean up expired sessions
            manager.cleanupExpiredSessions()

            # Check if session ID is valid
            if not manager.isSessionValid(session_id):
                error_msg = "Invalid or expired session ID. Please provide a valid session ID."
                Log.error(error_msg)
                return JSONResponse(
                    status_code=401,
                    content={"message": error_msg},
                )

            # Update last activity timestamp for the session
            manager.updateLastActivity(session_id)

            # Attach session ID to request state for downstream access
            request.state.session_id = session_id
            Log.info(f"Session ID '{session_id}' successfully made a request to endpoint '{request.url.path}'.")

            # Proceed to next middleware or route handler
            return await call_next(request)

        except Exception as e:
            # Handle exceptions during request processing
            error_msg = (
                "An error occurred while processing the request."
            )
            Log.error(f"{error_msg} Error details: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "message": error_msg,
                    "error": str(e),
                },
            )