from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from request.request_payload import HTTPRequestPayload
from response.api_response import APIResponse
from services.sesion_manager import SessionManager
from services.env import Env
import requests

# Initialize the singleton SessionManager instance
# Session timeout is configurable via environment variable (default: 30 minutes)
session_manager = SessionManager(
    session_timeout=int(Env.get("SESSION_TIMEOUT", 60 * 30))
)

# Define API router with grouped tags and descriptions
proxy_router = APIRouter()

@proxy_router.get(
    "/health-check",
    summary="Service Health Check",
    description="""Checks the status of the server and internet connectivity.

                   This endpoint performs the following checks:
                   - HTTPServerProxy server status
                   - Internet connectivity by making a request to Google
                   - Configured HTTP session status
                   - Operating system information

                   **Response codes:**
                   - 200: Service running correctly with internet access
                   - 503: Service running but no internet connectivity
                """,
    tags=["System"]
)
def health(request: Request) -> JSONResponse:
    """
    Check the health status of the service and internet connectivity.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.

    Returns
    -------
    JSONResponse
        JSON response indicating service and internet connectivity status.
    """

    STATUS_OK = "OK"
    STATUS_UNAVAILABLE = "Service Unavailable"

    try:

        # Attempt to reach Google to verify internet connectivity
        response = requests.get(
            "https://www.google.com",
            timeout=5,
            allow_redirects=True
        )

        if response.status_code == 200:
            return JSONResponse(
                status_code=200,
                content={
                    "status": STATUS_OK,
                    "internet": True,
                    "detail": "Internet connection available",
                    "response_time_ms": round(
                        response.elapsed.total_seconds() * 1000, 2
                    ),
                },
            )
        else:
            error_msg = (
                f"Unexpected response from Google: HTTP {response.status_code}"
            )
            return JSONResponse(
                status_code=503,
                content={
                    "status": STATUS_UNAVAILABLE,
                    "internet": False,
                    "detail": error_msg,
                },
            )

    except requests.exceptions.Timeout:
        error_msg = "Timeout connecting to google.com"
        return JSONResponse(
            status_code=503,
            content={
                "status": STATUS_UNAVAILABLE,
                "internet": False,
                "detail": error_msg,
            },
        )
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error - Check network configuration"
        return JSONResponse(
            status_code=503,
            content={
                "status": STATUS_UNAVAILABLE,
                "internet": False,
                "detail": error_msg,
            },
        )
    except Exception:
        error_msg = "Internal server error while checking connectivity"
        return JSONResponse(
            status_code=503,
            content={
                "status": STATUS_UNAVAILABLE,
                "internet": False,
                "detail": error_msg,
            },
        )

@proxy_router.post(
    "/set-headers",
    summary="Set Custom Session Headers",
    description=(
        "Sets custom headers for the global HTTP session.\n\n"
        "This endpoint allows you to define additional headers that will be "
        "included in all subsequent requests made through the proxy session.\n\n"
        "**Response codes:**\n"
        "- 200: Headers set successfully\n"
        "- 400: Invalid header format"
    ),
    response_model=dict[str, str],
    tags=["Session"],
)
def set_headers(
    request: Request, payload: dict[str, str]
) -> JSONResponse:
    """
    Set custom headers for the global HTTP session.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.
    payload : dict[str, str]
        Dictionary of header key-value pairs to set.

    Returns
    -------
    JSONResponse
        JSON response indicating the result of setting headers.
    """
    # Validate that payload is a dictionary of string key-value pairs
    if not isinstance(payload, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in payload.items()
    ):
        error_msg = "Headers must be a dictionary of string key-value pairs"
        return JSONResponse(
            status_code=400,
            content={"detail": error_msg},
        )

    # Retrieve the session instance from the request state
    session = session_manager.getSessionInstance(
        request.state.session_id
    )

    # Reset and update session headers if session is available in request state
    session.headers.clear()
    session.headers.update(payload)

    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "detail": "Custom headers set successfully",
        },
    )

@proxy_router.post(
    "/get-headers",
    summary="Get Current Session Headers",
    description=(
        "Retrieves the current headers set in the global HTTP session.\n\n"
        "This endpoint allows you to view all headers that are currently "
        "configured for the session, which will be included in all subsequent "
        "requests.\n\n"
        "**Response codes:**\n"
        "- 200: Headers retrieved successfully"
    ),
    response_model=dict[str, str],
    tags=["Session"],
)
def get_headers(request: Request) -> JSONResponse:
    """
    Retrieve the current headers set in the global HTTP session.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.

    Returns
    -------
    JSONResponse
        JSON response containing the current session headers.
    """
    # Get the session instance for the current request
    session = session_manager.getSessionInstance(request.state.session_id)

    # Return the current session headers
    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "headers": dict(session.headers),
        },
    )

@proxy_router.post(
    "/get-cookies",
    summary="Get Current Session Cookies",
    description=(
        "Retrieves the current cookies stored in the global HTTP session.\n\n"
        "This endpoint allows you to view all cookies that are currently stored "
        "in the session, which will be included in all subsequent requests.\n\n"
        "**Response codes:**\n"
        "- 200: Cookies retrieved successfully"
    ),
    response_model=dict[str, dict],
    tags=["Session"],
)
def get_cookies(request: Request) -> JSONResponse:
    """
    Retrieve the current cookies stored in the global HTTP session.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.

    Returns
    -------
    JSONResponse
        JSON response containing the current session cookies.
    """
    # Get the session instance for the current request
    session = session_manager.getSessionInstance(request.state.session_id)

    # Return the current session cookies as a list of dictionaries
    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "cookies": [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                }
                for c in session.cookies
            ],
        },
    )

@proxy_router.post(
    "/get-session-info",
    summary="Get Session Information",
    description=(
        "Retrieves detailed information about the current HTTP session.\n\n"
        "This endpoint provides insights into the session state, including cookies, "
        "headers, and other relevant metadata.\n\n"
        "**Response codes:**\n"
        "- 200: Session information retrieved successfully"
    ),
    response_model=dict[str, Any],
    tags=["Session"],
)
def get_session_info(request: Request) -> JSONResponse:
    """
    Retrieve detailed information about the current HTTP session.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.

    Returns
    -------
    JSONResponse
        JSON response containing session cookies, headers, and SSL verification
        status.
    """
    # Get the session instance for the current request
    session = session_manager.getSessionInstance(request.state.session_id)

    # Build session information dictionary
    session_info = {
        "cookies": [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
            }
            for c in session.cookies
        ],
        "headers": dict(session.headers),
        "verify_ssl": session.verify,
    }

    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "info": session_info,
        },
    )

@proxy_router.post(
    "/subscribe",
    summary="Subscribe to the proxy and create a work session",
    description=(
        "Create a unique work session for the client connecting to the proxy."
    ),
    response_model=dict[str, dict],
    tags=["Authentication"]
)
def subscribe(request: Request) -> JSONResponse:
    """
    Create a unique work session for the client.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.
    payload : LoginPayload
        The login payload containing authentication data.

    Returns
    -------
    JSONResponse
        JSON response with session information or error details.
    """
    try:

        # Create a new session for the client using user agent and IP address
        session_id = session_manager.createSession(
            user_agent=request.headers.get("User-Agent", "unknown"),
            client_ip=request.client.host,
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "OK",
                "session": {
                    "session_id": session_id
                }
            }
        )
    except Exception as e:

        # Handle any unexpected error during login
        error_msg = f"Unexpected error during login: {str(e)}"
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
            }
        )

@proxy_router.post(
    "/unsubscribe",
    summary="Unsubscribe from the proxy and remove session data",
    description=(
        "Performs the opposite of subscribe, removing the current work session."
    ),
    response_model=dict[str, str],
    tags=["Authentication"]
)
def unsubscribe(request: Request) -> JSONResponse:
    """
    Unsubscribe from the proxy and remove the current session.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.

    Returns
    -------
    JSONResponse
        JSON response indicating the result of the unsubscribe operation.
    """
    # If session ID is available in request state, delete the session
    if hasattr(request.state, "session_id"):
        session_manager.deleteSession(request.state.session_id)

    # Return success response
    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "detail": "Session cookies and headers cleared"
        }
    )

@proxy_router.post(
    "/forward",
    summary="HTTP Request Proxy",
    description="""Forwards HTTP requests while maintaining active session and cookies.

                   This endpoint acts as a transparent proxy that:
                   - Automatically maintains session cookies from login
                   - Preserves authentication headers
                   - Supports all standard HTTP methods
                   - Handles redirects and errors intelligently
                   - Provides detailed timing and performance information

                   **Proxy features:**
                   - ✅ Persistent session with automatic cookies
                   - ✅ Per-request customizable headers
                   - ✅ Support for form data and JSON
                   - ✅ Robust timeout and error handling
                   - ✅ Detailed logging for debugging
                   - ✅ Preservation of redirects and history

                   **Workflow:**
                   1. Receives parameters for the request to forward
                   2. Merges session cookies with additional cookies
                   3. Executes the request using the authenticated session
                   4. Returns a complete response with metadata
                """,
    response_model=APIResponse,
    tags=["Proxy"]
)
def forward(
    request: Request,
    payload: HTTPRequestPayload,
) -> JSONResponse:
    """
    Forward an HTTP request while maintaining session and cookies.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.
    payload : HTTPRequestPayload
        The payload containing HTTP request details.

    Returns
    -------
    JSONResponse
        A JSON response containing the proxied HTTP response data and metadata.
    """
    try:
        # Retrieve the session instance for the current request
        session = session_manager.getSessionInstance(
            request.state.session_id
        )

        # Merge session headers with custom headers from payload
        request_headers = session.headers.copy()
        if payload.headers:
            request_headers.update(payload.headers)

        # Merge session cookies with additional cookies from payload
        if payload.cookies and isinstance(payload.cookies, dict):
            for name, data in payload.cookies.items():
                session.cookies.set(
                    name,
                    data["value"],
                    domain=data.get("domain"),
                    path=data.get("path"),
                )

        # Execute HTTP request using the configured session
        response = session.request(
            method=payload.method,
            url=payload.url,
            params=payload.params,
            data=payload.data,
            json=payload.json_data,
            headers=request_headers,
            timeout=payload.timeout,
            allow_redirects=payload.allow_redirects,
        )

        # Update session cookies with any new cookies received in the response
        if response.cookies:
            session.cookies.update(response.cookies)

        # Build detailed response data for the client
        response_data = {
            "status": response.reason or "OK",
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "cookies": [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                }
                for c in response.cookies
            ],
            "session_cookies": [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                }
                for c in session.cookies
            ],
            "url": str(response.url),
            "elapsed": round(response.elapsed.total_seconds(), 3),
            "encoding": response.encoding,
            "ok": response.ok,
            "history": [str(r.url) for r in response.history],
            "content_type": response.headers.get("content-type", "unknown"),
            "body": response.text,
            "request_info": {
                "method": payload.method,
                "original_url": payload.url,
                "final_url": str(response.url),
                "redirects_count": len(response.history),
                "request_size_bytes": len(
                    str(payload.data or payload.json_data or "")
                ),
                "response_size_bytes": len(response.content),
            },
        }

        # Return the detailed response data to the client
        return JSONResponse(
            status_code=response.status_code,
            content=response_data,
        )

    except requests.exceptions.Timeout:
        # Handle request timeout exception
        error_msg = (
            f"Timeout while making request to {payload.url} after {payload.timeout}s"
        )
        return JSONResponse(
            status_code=408,
            content={
                "error": error_msg,
                "error_type": "TimeoutError",
                "url": payload.url,
                "timeout": payload.timeout,
                "method": payload.method,
            },
        )
    except requests.exceptions.ConnectionError as e:
        # Handle connection error exception
        error_msg = f"Connection error while forwarding request: {str(e)}"
        return JSONResponse(
            status_code=502,
            content={
                "error": error_msg,
                "error_type": "ConnectionError",
                "url": payload.url,
                "method": payload.method,
            },
        )
    except requests.exceptions.HTTPError as e:
        # Handle HTTP error exception
        error_msg = f"HTTP error while forwarding request: {str(e)}"
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "error_type": "HTTPError",
                "url": payload.url,
                "method": payload.method,
            },
        )
    except Exception as e:
        # Handle any other unexpected exceptions
        error_msg = f"Unexpected error while forwarding request: {str(e)}"
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "error_type": type(e).__name__,
                "url": payload.url,
                "method": payload.method,
            },
        )

@proxy_router.post(
    "/dowwnload",
    summary="File Download Proxy",
    description="Download files while maintaining session and cookies.",
    tags=["Proxy"],
    response_model=None
)
def download(
    request: Request,
    payload: HTTPRequestPayload,
):
    """
    Download a file using the authenticated session and return it as a direct download.

    Parameters
    ----------
    request : Request
        The incoming FastAPI request object.
    payload : HTTPRequestPayload
        The payload containing HTTP request details.

    Returns
    -------
    StreamingResponse or JSONResponse
        Returns a StreamingResponse for file download or a JSONResponse with
        error details if the download fails.
    """
    try:
        # Retrieve the session instance for the current request
        session = session_manager.getSessionInstance(
            request.state.session_id
        )

        # Merge session headers with custom headers from payload
        request_headers = session.headers.copy()
        if payload.headers:
            request_headers.update(payload.headers)

        # Merge session cookies with additional cookies from payload
        if payload.cookies and isinstance(payload.cookies, dict):
            for name, data in payload.cookies.items():
                session.cookies.set(
                    name,
                    data["value"],
                    domain=data.get("domain"),
                    path=data.get("path"),
                )

        # Execute HTTP request using the configured session, streaming response
        response = session.request(
            method=payload.method,
            url=payload.url,
            params=payload.params,
            data=payload.data,
            json=payload.json_data,
            headers=request_headers,
            timeout=payload.timeout,
            allow_redirects=payload.allow_redirects,
            stream=True,
        )

        # Update session cookies with any new cookies received in the response
        if response.cookies:
            session.cookies.update(response.cookies)

        # Get content type and suggested filename from response headers
        content_type = response.headers.get(
            "content-type", "application/octet-stream"
        )
        content_disp = response.headers.get("content-disposition")
        filename = "downloaded_file"
        if content_disp:
            import re
            match = re.search(r'filename="?([^";]+)"?', content_disp)
            if match:
                filename = match.group(1)

        # Return file as a direct download using StreamingResponse
        return StreamingResponse(
            response.iter_content(chunk_size=8192),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except requests.exceptions.Timeout:
        error_msg = (
            f"Timeout while making request to {payload.url} after {payload.timeout}s"
        )
        return JSONResponse(
            status_code=408,
            content={
                "error": error_msg,
                "error_type": "TimeoutError",
                "url": payload.url,
                "timeout": payload.timeout,
            },
        )
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error during file download: {str(e)}"
        return JSONResponse(
            status_code=502,
            content={
                "error": error_msg,
                "error_type": "ConnectionError",
                "url": payload.url,
            },
        )
    except Exception as e:
        error_msg = f"Unexpected error during file download: {str(e)}"
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "error_type": type(e).__name__,
                "url": payload.url,
            },
        )
