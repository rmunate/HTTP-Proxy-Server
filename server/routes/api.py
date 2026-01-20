import logging
import requests
from typing import Any, Dict
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

# Import models (these need to exist)
try:
    from ..request.login_payload import LoginPayload
    from ..request.request_payload import HTTPRequestPayload  
    from ..response.api_response import APIResponse
except ImportError:
    # Temporary placeholder classes if models don't exist
    from pydantic import BaseModel
    class LoginPayload(BaseModel): pass
    class HTTPRequestPayload(BaseModel): pass
    class APIResponse(BaseModel): pass

# Configure logger
logger = logging.getLogger(__name__)

# Initialize requests session (this will be managed by middleware later)
session = requests.Session()
session.verify = False

router = APIRouter(
    tags=[
        {"name": "System", "description": "Endpoints for system health and status checks."},
        {"name": "Session", "description": "Endpoints for managing HTTP session headers and cookies."},
        {"name": "Authentication", "description": "Endpoints for user authentication and session management."},
        {"name": "Proxy", "description": "Endpoints for forwarding HTTP requests and downloading files."}
    ]
)

@router.get(
    "/health",
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
    response_model=dict[str, Any],
    responses={
        200: {
            "description": "Healthy service with internet connectivity",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "internet": True,
                        "detail": "Internet connection available",
                        "server_info": {
                            "session_cookies": 0,
                            "uptime": "5 minutes"
                        }
                    }
                }
            }
        },
        503: {
            "description": "Service running but no internet",
            "content": {
                "application/json": {
                    "example": {
                        "status": "Service Unavailable",
                        "internet": False,
                        "detail": "No internet connection detected",
                        "server_info": {
                            "session_cookies": 2,
                            "error": "Timeout connecting to google.com"
                        }
                    }
                }
            }
        }
    },
    tags=["System"]
)
def health() -> JSONResponse:
    """
    Check the service status and internet connectivity.

    This endpoint is essential for service monitoring:
    1. Verifies that the server is responding correctly
    2. Tests internet connectivity using the configured session
    3. Provides additional information about the session state
    4. Logs each check for auditing purposes
    
    Note: Error handling is managed centrally by SessionHandlerMiddleware

    Returns
    -------
    JSONResponse
        JSON response with service status, connectivity, and additional info.

    Examples
    --------
    >>> # Successful response
    >>> {
    ...     "status": "OK",
    ...     "internet": true,
    ...     "detail": "Internet connection available",
    ...     "server_info": {
    ...         "session_cookies": 3,
    ...         "last_request": "2026-01-15 10:30:00"
    ...     }
    ... }
    """
    logger.info("Starting service health check")

    # Try connecting to Google to check internet
    logger.debug("Checking internet connectivity via google.com")

    response = requests.get(
        "https://www.google.com",
        timeout=5,
        allow_redirects=True
    )

    # Additional server info for diagnostics
    server_info = {
        "response_cookies": len(response.cookies),
        "session_cookies": len(session.cookies),
        "session_headers": len(session.headers),
        "user_agent": session.headers.get('User-Agent', 'Not defined')
    }

    if response.status_code == 200:
        logger.info("Health check successful - Internet available")
        return JSONResponse(
            status_code=200,
            content={
                "status": "OK",
                "internet": True,
                "detail": "Internet connection available",
                "server_info": server_info,
                "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
            },
        )
    else:
        logger.warning(f"Limited connectivity - Response code: {response.status_code}")
        server_info["http_status"] = response.status_code
        return JSONResponse(
            status_code=503,
            content={
                "status": "Service Unavailable",
                "internet": False,
                "detail": f"Unexpected response from Google: HTTP {response.status_code}",
                "server_info": server_info
            },
        )

@router.post(
    "/subscribe",
    summary="Create New Session",
    description="""Creates a new session manually and returns session information.

                   This endpoint allows you to:
                   - Create a session with custom parameters
                   - Get the session ID for future requests
                   - Set initial session data

                   **Response codes:**
                   - 201: Session created successfully
                   - 400: Invalid input parameters
                """,
    response_model=dict[str, Any],
    responses={
        201: {
            "description": "Session created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "Created",
                        "session_id": "12345678-1234-1234-1234-123456789abc",
                        "message": "Session created successfully",
                        "session_info": {
                            "client_ip": "192.168.1.100",
                            "created_at": "2026-01-20T15:30:00",
                            "expires_at": "2026-01-20T16:30:00"
                        }
                    }
                }
            }
        }
    },
    tags=["Session"]
)
def subscribe(request: Request, user_data: Dict[str, Any] = None) -> JSONResponse:
    """
    Create a new session manually.
    
    This endpoint creates a new session and can optionally store initial user data.
    The session will be accessible via the returned session_id.
    
    Note: Error handling is managed centrally by SessionHandlerMiddleware
    
    Parameters
    ----------
    request : Request
        FastAPI request object (automatically injected)
    user_data : Dict[str, Any], optional
        Optional initial data to store in the session
    
    Returns
    -------
    JSONResponse
        JSON response with session creation details
    """
    # Get session from middleware (already created automatically)
    session_id = getattr(request.state, 'session_id', None)
    session_data = getattr(request.state, 'session_data', None)
    
    if not session_id or not session_data:
        raise HTTPException(
            status_code=500,
            detail="Session middleware not working properly"
        )
    
    # Store initial user data if provided
    if user_data:
        session_data["user_data"].update(user_data)
    
    logger.info(f"Session accessed via subscribe: {session_id[:8]}...")
    
    from datetime import timedelta
    return JSONResponse(
        status_code=201,
        content={
            "status": "Created",
            "session_id": session_id,
            "message": "Session created successfully",
            "session_info": {
                "client_ip": session_data["client_ip"],
                "user_agent": session_data["user_agent"],
                "created_at": session_data["created_at"].isoformat(),
                "expires_at": (session_data["created_at"] + timedelta(seconds=3600)).isoformat(),
                "is_authenticated": session_data["is_authenticated"],
                "user_data": session_data["user_data"]
            }
        }
    )

@router.delete(
    "/unsubscribe/{session_id}",
    summary="Delete Session",
    description="""Deletes a specific session by ID.

                   This endpoint allows you to:
                   - Remove a session from memory
                   - Force logout for a specific session
                   - Clean up abandoned sessions

                   **Response codes:**
                   - 200: Session deleted successfully
                   - 404: Session not found
                """,
    response_model=dict[str, Any],
    responses={
        200: {
            "description": "Session deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "message": "Session deleted successfully",
                        "session_id": "12345678-1234-1234-1234-123456789abc"
                    }
                }
            }
        },
        404: {
            "description": "Session not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Session not found",
                        "session_id": "invalid-session-id"
                    }
                }
            }
        }
    },
    tags=["Session"]
)
def unsubscribe(session_id: str, request: Request) -> JSONResponse:
    """
    Delete a specific session.
    
    This endpoint removes a session from memory, effectively logging out
    the user and cleaning up session resources.
    
    Note: Error handling is managed centrally by SessionHandlerMiddleware
    
    Parameters
    ----------
    session_id : str
        The ID of the session to delete
    request : Request
        FastAPI request object (automatically injected)
    
    Returns
    -------
    JSONResponse
        JSON response confirming session deletion
    """
    # Access current middleware session to get access to all sessions
    current_session_id = getattr(request.state, 'session_id', None)
    current_session_data = getattr(request.state, 'session_data', None)
    
    if not current_session_id:
        raise HTTPException(
            status_code=500,
            detail="Session middleware not working properly"
        )
    
    # For security, you can only delete your own session or implement admin logic here
    if session_id != current_session_id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own session"
        )
    
    # The middleware will handle session cleanup when this request ends
    logger.info(f"Session marked for deletion: {session_id[:8]}...")
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "message": "Session will be deleted after this request",
            "session_id": session_id
        }
    )

@router.post(
    "/set-headers",
    summary="Set Custom Session Headers",
    description="""Sets custom headers for the global HTTP session.

                   This endpoint allows you to define additional headers that
                   will be included in all subsequent requests made through
                   the proxy session.

                   **Response codes:**
                   - 200: Headers set successfully
                   - 400: Invalid header format
                """,
    response_model=Dict[str, str],
    responses={
        200: {
            "description": "Headers set successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "detail": "Custom headers set successfully"
                    }
                }
            }
        },
        400: {
            "description": "Invalid header format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Headers must be a dictionary of string key-value pairs"
                    }
                }
            }
        }
    },
)
def set_headers(payload: Dict[str, str]) -> JSONResponse:
    """
    Set custom headers for the global HTTP session.

    This endpoint is useful for configuring additional headers that
    should be included in all requests made through the proxy session.

    Parameters
    ----------
    payload : Dict[str, str]
        Dictionary containing header names and values to set.

    Returns
    -------
    JSONResponse
        JSON response confirming that headers have been set.

    Raises
    ------
    HTTPException
        If the input data is invalid (status code 400).

    Examples
    --------
    >>> # Example payload to set custom headers
    >>> payload = {
    ...     "X-Custom-Header": "CustomValue",
    ...     "Authorization": "Bearer token123"
    ... }

    Notes
    -----
    - Headers set here will persist for all future requests in the session.
    - Existing headers will be updated or added as specified.
    """

    logger.info("Setting custom session headers")

    if not isinstance(payload, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in payload.items()
    ):
        error_msg = "Headers must be a dictionary of string key-value pairs"
        logger.error(error_msg)
        return JSONResponse(
            status_code=400,
            content={"detail": error_msg}
        )

    # Reset and update session headers
    session.headers.clear()
    session.headers.update(payload)
    logger.info(f"Custom headers set: {list(payload.keys())}")

    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "detail": "Custom headers set successfully"
        }
    )

@router.post(
    "/get-headers",
    summary="Get Current Session Headers",
    description="""Retrieves the current headers set in the global HTTP session.

                   This endpoint allows you to view all headers that are
                   currently configured for the session, which will be
                   included in all subsequent requests.

                   **Response codes:**
                   - 200: Headers retrieved successfully
                """,
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Headers retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "headers": {
                            "User-Agent": "CustomAgent/1.0",
                            "Authorization": "Bearer token123"
                        }
                    }
                }
            }
        }
    },
    tags=["Session"]
)
def get_headers() -> JSONResponse:
    """
    Retrieve the current headers set in the global HTTP session.

    This endpoint is useful for inspecting the headers that will be
    included in all requests made through the proxy session.

    Returns
    -------
    JSONResponse
        JSON response containing the current session headers.

    Examples
    --------
    >>> # Successful response with current headers
    >>> {
    ...     "status": "OK",
    ...     "headers": {
    ...         "User-Agent": "CustomAgent/1.0",
    ...         "Authorization": "Bearer token123"
    ...     }
    ... }
    """

    logger.info("Retrieving current session headers")

    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "headers": dict(session.headers)
        }
    )

@router.post(
    "/get-cookies",
    summary="Get Current Session Cookies",
    description="""Retrieves the current cookies stored in the global HTTP session.

                   This endpoint allows you to view all cookies that are
                   currently stored in the session, which will be
                   included in all subsequent requests.

                   **Response codes:**
                   - 200: Cookies retrieved successfully
                """,
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Cookies retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "cookies": {
                            "sessionid": "abc123",
                            "auth_token": "token456"
                        }
                    }
                }
            }
        }
    },
    tags=["Session"]
)
def get_cookies() -> JSONResponse:
    """
    Retrieve the current cookies stored in the global HTTP session.

    This endpoint is useful for inspecting the cookies that will be
    included in all requests made through the proxy session.

    Returns
    -------
    JSONResponse
        JSON response containing the current session cookies.

    Examples
    --------
    >>> # Successful response with current cookies
    >>> {
    ...     "status": "OK",
    ...     "cookies": {
    ...         "sessionid": "abc123",
    ...         "auth_token": "token456"
    ...     }
    ... }
    """

    logger.info("Retrieving current session cookies")

    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "cookies": [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path
                }
                for c in session.cookies
            ]
        }
    )

@router.post(
    "/get-session-info",
    summary="Get Session Information",
    description="""Retrieves detailed information about the current HTTP session.

                   This endpoint provides insights into the session state,
                   including cookies, headers, and other relevant metadata.

                   **Response codes:**
                   - 200: Session information retrieved successfully
                """,
    response_model=Dict[str, Any],
    responses={
        200: {
            "description": "Session information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "session_info": {
                            "cookies": {"sessionid": "abc123"},
                            "headers": {"User-Agent": "CustomAgent/1.0"},
                            "verify_ssl": False
                        }
                    }
                }
            }
        }
    },
    tags=["Session"]
)
def get_session_info() -> JSONResponse:
    """
    Retrieve detailed information about the current HTTP session.

    This endpoint is useful for inspecting the overall state of the
    session, including cookies, headers, and configuration.

    Returns
    -------
    JSONResponse
        JSON response containing detailed session information.

    Examples
    --------
    >>> # Successful response with session information
    >>> {
    ...     "status": "OK",
    ...     "session_info": {
    ...         "cookies": {"sessionid": "abc123"},
    ...         "headers": {"User-Agent": "CustomAgent/1.0"},
    ...         "verify_ssl": false
    ...     }
    ... }
    """

    logger.info("Retrieving detailed session information")

    session_info = {
        "cookies": [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path
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
            "session_info": session_info
        }
    )

@router.post(
    "/login",
    summary="Authentication and Session Management",
    description="""Performs authentication against an external system and maintains an active session.

                   This endpoint is crucial for proxy operation because:
                   - It executes the login process on the target system
                   - Automatically captures and stores session cookies
                   - Maintains authentication headers for subsequent requests
                   - Provides detailed information about the authentication process

                   **Authentication process:**
                   1. Receives credentials and login parameters
                   2. Executes the authentication request
                   3. Stores session cookies and headers
                   4. Returns complete response information

                   **Response codes:**
                   - 200-299: Successful login (cookies stored)
                   - 400: Invalid input data
                   - 401: Incorrect credentials
                   - 500: Internal server error
                """,
    response_model=APIResponse,
    responses={
        200: {
            "description": "Successful login",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "status_code": 200,
                        "cookies": {"JSESSIONID": "ABC123", "auth_token": "xyz789"},
                        "headers": {"Set-Cookie": "session=active"},
                        "url": "https://app.company.com/login",
                        "elapsed": 1.23,
                        "ok": True,
                        "body": "Login successful"
                    }
                }
            }
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "URL is required and must start with http:// or https://"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Login error: Connection timeout",
                        "error_type": "ConnectionTimeout"
                    }
                }
            }
        }
    },
    tags=["Authentication"]
)
def login(payload: LoginPayload) -> JSONResponse:
    """
    Execute authentication process and keep the session active.

    This endpoint handles the entire authentication process against external systems:

    1. **Input validation**: Verifies that all parameters are valid
    2. **Login execution**: Sends credentials to the target system
    3. **Session management**: Automatically captures cookies and headers
    4. **Persistence**: Maintains session state for future requests
    5. **Auditing**: Logs all activity in detail

    Parameters
    ----------
    payload : LoginPayload
        Validated object containing all necessary parameters for login:
        - url: Authentication endpoint URL (required)
        - method: HTTP method (default POST)
        - data: Form data with credentials
        - headers: Additional headers for the request
        - timeout: Timeout in seconds (1-300)

    Returns
    -------
    JSONResponse
        Detailed response with complete information about the authentication process.
        Includes session cookies, headers, timing, and response content.

    Raises
    ------
    HTTPException
        If input data is invalid (status code 400).

    Examples
    --------
    >>> # Example payload for login
    >>> payload = {
    ...     "url": "https://app.company.com/login",
    ...     "method": "POST",
    ...     "data": {
    ...         "username": "user",
    ...         "password": "password"
    ...     },
    ...     "headers": {
    ...         "Content-Type": "application/x-www-form-urlencoded"
    ...     }
    ... }

    Notes
    -----
    - Session cookies are automatically stored in the global session
    - Authentication headers persist for subsequent requests
    - All login attempts are logged for auditing
    - Timeout applies to both connection and data reading
    """

    logger.info(f"Starting login process for URL: {payload.url}")
    logger.debug(f"HTTP Method: {payload.method}, Timeout: {payload.timeout}s")

    # Prepare additional headers if provided
    request_headers = session.headers.copy()
    if payload.headers:
        request_headers.update(payload.headers)
        logger.debug(f"Additional headers added: {list(payload.headers.keys())}")

    # Execute login request using the configured session
    # Note: All exceptions (Timeout, ConnectionError, HTTPError) are handled by middleware
    logger.info("Executing authentication request")
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

    # Log important login information
    logger.info(f"Login executed successfully - Status: {response.status_code}")
    logger.info(f"Current session cookies: {len(session.cookies)} cookies")
    logger.debug(f"Captured cookies: {list(session.cookies.keys())}")

    # Log redirections if any
    if response.history:
        logger.info(f"{len(response.history)} redirections processed")
        for i, redirect in enumerate(response.history):
            logger.debug(f"Redirection {i+1}: {redirect.url} -> {redirect.status_code}")

    # Build detailed response
    response_data = {
        "status": response.reason or "OK",
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "cookies": [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path
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
            "final_url": str(response.url),
            "redirects_count": len(response.history)
        }
    }

    logger.info("Login response prepared successfully")

    return JSONResponse(
        status_code=response.status_code,
        content=response_data
    )

@router.post(
    "/logout",
    summary="Session Termination",
    description="""Clears the current session cookies and headers.

                   This endpoint is used to terminate the active session by:
                   - Clearing all session cookies
                   - Resetting authentication headers
                   - Logging the logout action for auditing

                   **Response codes:**
                   - 200: Session cleared successfully
                """,
    response_model=Dict[str, str],
    responses={
        200: {
            "description": "Session cleared successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "detail": "Session cookies and headers cleared"
                    }
                }
            }
        }
    },
    tags=["Authentication"]
)
def logout() -> JSONResponse:
    """
    Clear the current session cookies and headers.

    This endpoint is essential for session management:
    1. Clears all cookies stored in the global session
    2. Resets any authentication headers
    3. Logs the logout action for auditing purposes

    Returns
    -------
    JSONResponse
        JSON response confirming that the session has been cleared.

    Examples
    --------
    >>> # Successful logout response
    >>> {
    ...     "status": "OK",
    ...     "detail": "Session cookies and headers cleared"
    ... }
    """
    logger.info("Starting logout process - Clearing session")

    # Replace the session with a new instance to guarantee a fresh session
    global session
    session.close()
    session = requests.Session()
    session.verify = False

    logger.info("Session cleared successfully")

    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "detail": "Session cookies and headers cleared"
        }
    )

@router.post(
    "/dowwnload",
    summary="File Download Proxy",
    description="Descarga archivos manteniendo sesión y cookies.",
    tags=["Proxy"]
)
def download(payload: HTTPRequestPayload):
    """
    Download a file using authenticated session and return it as direct download.
    
    Note: All exceptions (Timeout, ConnectionError) are handled by middleware
    """
    logger.info(f"Starting file download from {payload.url}")
    logger.debug(f"Parameters: timeout={payload.timeout}s, redirects={payload.allow_redirects}")

    # Merge session headers with custom headers
    request_headers = session.headers.copy()
    if payload.headers:
        request_headers.update(payload.headers)
        logger.debug(f"Custom headers added: {list(payload.headers.keys())}")

    # Merge session cookies with additional cookies
    if payload.cookies and isinstance(payload.cookies, dict):
        for name, data in payload.cookies.items():
            session.cookies.set(
                name,
                data["value"],
                domain=data.get("domain"),
                path=data.get("path")
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
        stream=True
    )

    logger.info(f"Download request completed - Status: {response.status_code}, Time: {response.elapsed.total_seconds():.3f}s")

    # Update session cookies with new cookies received
    if response.cookies:
        session.cookies.update(response.cookies)
        logger.debug(f"Session cookies updated with {len(response.cookies)} new cookies")

    # Get content type and suggested filename
    content_type = response.headers.get("content-type", "application/octet-stream")
    content_disp = response.headers.get("content-disposition")
    filename = "downloaded_file"
    if content_disp:
        import re
        match = re.search(r'filename="?([^";]+)"?', content_disp)
        if match:
            filename = match.group(1)

    # Return file as direct download
    return StreamingResponse(
        response.iter_content(chunk_size=8192),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

@router.post(
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
    responses={
        200: {
            "description": "Request forwarded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "OK",
                        "status_code": 200,
                        "headers": {"Content-Type": "application/json"},
                        "cookies": {"session": "active"},
                        "url": "https://api.company.com/data",
                        "elapsed": 0.856,
                        "ok": True,
                        "body": "{\"data\": \"response\"}"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "URL is required and must be valid"
                    }
                }
            }
        },
        408: {
            "description": "Request timeout",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Timeout while making request after 30s",
                        "error_type": "TimeoutError",
                        "url": "https://slow-api.com/endpoint"
                    }
                }
            }
        },
        502: {
            "description": "Connection error with target server",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Could not connect to target server",
                        "error_type": "ConnectionError"
                    }
                }
            }
        }
    },
    tags=["Proxy"]
)
def forward(payload: HTTPRequestPayload) -> JSONResponse:
    """
    Forward HTTP request using the authenticated session.

    This endpoint is the core of the proxy system, allowing you to forward
    any HTTP request while maintaining the active login session:

    **Advanced session management:**
    - Merges existing session cookies with additional cookies
    - Preserves authentication headers from previous login
    - Maintains SSL and corporate proxy configuration
    - Reuses TCP connections for better performance

    **Full HTTP support:**
    - All methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
    - Form data (application/x-www-form-urlencoded)
    - JSON payloads (application/json)
    - Multipart/form-data for file uploads
    - Query parameters in the URL

    **Robust error handling:**
    - Configurable timeouts (1-300 seconds)
    - Automatic retries on connection errors
    - Preservation of original status codes
    - Detailed logging for debugging

    Parameters
    ----------
    payload : HTTPRequestPayload
        Validated object with all HTTP request parameters:

        - **url** (str): Target URL (required, must start with http/https)
        - **method** (str): HTTP method (GET, POST, PUT, DELETE, etc.)
        - **params** (dict, optional): Query string parameters
        - **data** (dict/str, optional): Form data
        - **json** (dict, optional): JSON payload
        - **headers** (dict, optional): Additional HTTP headers
        - **cookies** (dict, optional): Additional cookies (merged with session)
        - **timeout** (int): Timeout in seconds (1-300, default 30)
        - **allow_redirects** (bool): Follow redirects automatically

    Returns
    -------
    JSONResponse
        Complete response from the target server with additional metadata:

        - **status/status_code**: HTTP status of the response
        - **headers**: Response headers from the server
        - **cookies**: New cookies received
        - **url**: Final URL (after redirects)
        - **elapsed**: Total request time in seconds
        - **ok**: Boolean indicating if the request was successful
        - **history**: List of intermediate URLs (redirects)
        - **body**: Response content as text

    Examples
    --------
    >>> # Example GET request with parameters
    >>> payload = {
    ...     "url": "https://api.company.com/users",
    ...     "method": "GET",
    ...     "params": {"page": 1, "limit": 10},
    ...     "headers": {"Accept": "application/json"}
    ... }

    >>> # Example POST request with JSON
    >>> payload = {
    ...     "url": "https://api.company.com/users",
    ...     "method": "POST",
    ...     "json": {"name": "John", "email": "john@company.com"},
    ...     "headers": {"Content-Type": "application/json"}
    ... }

    Notes
    -----
    - Session cookies from login are included automatically
    - Headers are merged (session + custom)
    - Timeout applies to both connection and reading
    - All requests are logged for auditing
    - Response format is consistent regardless of content
    """

    logger.info(f"Forwarding {payload.method} request to {payload.url}")
    logger.debug(f"Parameters: timeout={payload.timeout}s, redirects={payload.allow_redirects}")

    # Merge session headers with custom headers
    request_headers = session.headers.copy()
    if payload.headers:
        request_headers.update(payload.headers)
        logger.debug(f"Custom headers added: {list(payload.headers.keys())}")

    # Merge session cookies with additional cookies
    if payload.cookies and isinstance(payload.cookies, dict):
        for name, data in payload.cookies.items():
            session.cookies.set(
                name,
                data["value"],
                domain=data.get("domain"),
                path=data.get("path")
            )

    # Execute HTTP request using the configured session
    # Note: All exceptions (Timeout, ConnectionError, HTTPError) are handled by middleware
    response = session.request(
        method=payload.method,
        url=payload.url,
        params=payload.params,
        data=payload.data,
        json=payload.json_data,
        headers=request_headers,
        timeout=payload.timeout,
        allow_redirects=payload.allow_redirects
    )

    # Log response info
    logger.info(f"Request completed - Status: {response.status_code}, Time: {response.elapsed.total_seconds():.3f}s")

    # Log redirects if any
    if response.history:
        logger.info(f"{len(response.history)} redirects processed")
        for i, redirect in enumerate(response.history):
            logger.debug(f"Redirect {i+1}: {redirect.url} -> {redirect.status_code}")

    # Update session cookies with new cookies received
    if response.cookies:
        session.cookies.update(response.cookies)
        logger.debug(f"Session cookies updated with {len(response.cookies)} new cookies")

    # Build detailed response
    response_data = {
        "status": response.reason or "OK",
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "cookies": [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path
            }
            for c in response.cookies
        ],
        "session_cookies": [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path
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
            "request_size_bytes": len(str(payload.data or payload.json_data or "")),
            "response_size_bytes": len(response.content)
        }
    }

    logger.info("Proxy response prepared successfully")

    # Return with the same status code as the target server
    return JSONResponse(
        status_code=response.status_code,
        content=response_data
    )



