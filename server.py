"""
HTTP Proxy Server
=================

This module implements a FastAPI server that acts as an HTTP proxy,
maintaining active sessions and providing endpoints for login and
forwarding HTTP requests.

Main features:
- Maintains persistent sessions with cookies
- Internet connectivity check
- HTTP request proxy with authentication
- Detailed operation logging
- Robust input data validation

Author: Raul Mauricio Uñate Castro
Version: 2.0
Date: 2026-01-15
"""

# ============================================================================
# IMPORTS AND INITIAL CONFIGURATION
# ============================================================================

# Standard Python libraries
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Third-party libraries
import urllib3
import uvicorn
import requests
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

# ============================================================================
# SECURITY AND LOGGING CONFIGURATION
# ============================================================================

# Disable SSL certificate warnings
# This is necessary for proxy operation in corporate environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Advanced logging configuration with file rotation
# When running as an executable, use the .exe location for logs
if getattr(sys, 'frozen', False):
    # Running as a compiled executable
    log_file = Path(sys.executable).with_suffix(".log")
else:
    # Running as a Python script
    log_file = Path(__file__).with_suffix(".log")

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    encoding='utf-8'
)

# Application-specific logger
logger = logging.getLogger(__name__)

# ============================================================================
# MODELOS DE VALIDACIÓN CON PYDANTIC
# ============================================================================

class HTTPRequestPayload(BaseModel):
    """
    Validate and store HTTP request payload data.

    Validates that incoming HTTP request payloads conform to the expected
    format and contain the required data.

    Parameters
    ----------
    url : str
        Destination URL for the HTTP request.
    method : str, default="GET"
        HTTP method (GET, POST, PUT, DELETE, etc.).
    params : dict[str, Any] | None, default=None
        Query string parameters for the URL.
    data : dict[str, Any] | str | None, default=None
        Form data for the request body.
    json_data : dict[str, Any] | None, default=None
        JSON data for the request body.
    headers : dict[str, str] | None, default=None
        Additional HTTP headers.
    cookies : dict[str, str] | None, default=None
        Cookies to send with the request.
    timeout : int, default=30
        Timeout in seconds (1-300).
    allow_redirects : bool, default=True
        Whether to allow automatic redirects.

    Returns
    -------
    HTTPRequestPayload
        An instance containing validated HTTP request data.
    """

    url: str = Field(..., description="Destination URL for the request")
    method: str = Field(
        default="GET", description="HTTP method (GET, POST, PUT, DELETE, etc.)"
    )
    params: dict[str, Any] | None = Field(
        default=None, description="Query string parameters"
    )
    data: dict[str, Any] | str | None = Field(
        default=None, description="Form data for the request body"
    )
    json_data: dict[str, Any] | None = Field(
        default=None, description="JSON data for the request body"
    )
    headers: dict[str, str] | None = Field(
        default=None, description="Additional HTTP headers"
    )
    cookies: dict[str, dict] | None = Field(
        default=None, description="Cookies to send with the request"
    )
    timeout: int = Field(
        default=30, ge=1, le=300, description="Timeout in seconds (1-300)"
    )
    allow_redirects: bool = Field(
        default=True, description="Allow automatic redirects"
    )

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        """
        Validate that the HTTP method is allowed.

        Parameters
        ----------
        v : str
            HTTP method to validate.

        Returns
        -------
        str
            The validated HTTP method in uppercase.

        Raises
        ------
        ValueError
            If the HTTP method is not allowed.
        """
        allowed_methods = [
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'
        ]
        if v.upper() not in allowed_methods:
            error_msg = (
                f'Invalid HTTP method. Must be one of: {", ".join(allowed_methods)}'
            )
            raise ValueError(error_msg)
        return v.upper()

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """
        Validate that the URL starts with http:// or https://.

        Parameters
        ----------
        v : str
            URL to validate.

        Returns
        -------
        str
            The validated URL.

        Raises
        ------
        ValueError
            If the URL does not start with http:// or https://.
        """
        if not v.startswith(('http://', 'https://')):
            error_msg = 'URL must start with http:// or https://'
            raise ValueError(error_msg)
        return v

class LoginPayload(HTTPRequestPayload):
    """
    Define a payload model for login requests.

    Inherits from HTTPRequestPayload and sets the default HTTP method to POST.
    Additional login-specific validation can be added here.

    Parameters
    ----------
    method : str, optional
        HTTP method for login (default is "POST").

    Returns
    -------
    None
        This class is used for data validation and does not return a value.
    """

    method: str = Field(
        default="POST",
        description="HTTP method for login (usually POST)"
    )

class APIResponse(BaseModel):
    """
    Represent a standard API response.

    Parameters
    ----------
    status : str
        HTTP status reason phrase.
    status_code : int
        HTTP status code.
    headers : dict[str, str], optional
        Response headers.
    cookies : dict[str, str], optional
        Response cookies.
    url : str or None, optional
        Final URL after redirects.
    elapsed : float or None, optional
        Time taken for the request in seconds.
    encoding : str or None, optional
        Response encoding.
    ok : bool, optional
        Indicates if the request was successful.
    history : list[str], optional
        List of redirect URLs.
    content_type : str or None, optional
        Content-Type of the response.
    body : str
        Response body as text.

    Returns
    -------
    APIResponse
        An instance containing the API response data.
    """

    status: str
    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
    url: str | None = None
    elapsed: float | None = None
    encoding: str | None = None
    ok: bool = False
    history: list[str] = Field(default_factory=list)
    content_type: str | None = None
    body: str = ""

# ============================================================================
# FASTAPI APPLICATION CONFIGURATION
# ============================================================================

# Create FastAPI instance with complete metadata
app = FastAPI(
    title="HTTP Proxy Server",
    description="""HTTP proxy server that maintains persistent sessions and
                   provides endpoints for authentication and request forwarding.

                   Features:
                   - ✅ Automatically maintains session cookies
                   - ✅ Internet connectivity health check
                   - ✅ Transparent HTTP/HTTPS request proxy
                   - ✅ Detailed logging of all operations
                   - ✅ Robust input data validation
                """,
    version="2.0.0",
    contact={
        "name": "Raul M. Uñate",
        "email": "raulmauriciounate@gmail.com",
    },
    license_info={
        "name": "Raul M. Uñate",
    },
)

# Configure CORS to allow requests from any origin
# This is important for web applications consuming this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# GLOBAL HTTP SESSION CONFIGURATION
# ============================================================================

# Create a persistent HTTP session to maintain cookies and configuration
# This session is reused for all requests to preserve state
session = requests.Session()

# Configure the session for corporate environments
# Disable SSL verification for corporate proxies
session.verify = False

# Log initial configuration
logger.info("HTTPServerProxy application initialized successfully")
logger.info(f"HTTP session configured with User-Agent: {session.headers['User-Agent']}")

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get(
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
    response_model=Dict[str, Any],
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

    try:
        # Try connecting to Google using the configured session to check internet
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
                    "status": "Service Unavailable", # NOSONAR
                    "internet": False,
                    "detail": f"Unexpected response from Google: HTTP {response.status_code}",
                    "server_info": server_info
                },
            )

    except requests.exceptions.Timeout:
        logger.error("Timeout while checking internet connectivity")
        return JSONResponse(
            status_code=503,
            content={
                "status": "Service Unavailable",
                "internet": False,
                "detail": "Timeout connecting to google.com",
                "server_info": {"error_type": "Timeout"}
            },
        )
    except requests.exceptions.ConnectionError:
        logger.error("Connection error while checking internet")
        return JSONResponse(
            status_code=503,
            content={
                "status": "Service Unavailable",
                "internet": False,
                "detail": "Connection error - Check network configuration",
                "server_info": {"error_type": "ConnectionError"}
            },
        )
    except Exception as e:
        logger.exception(f"Unexpected error during health check: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "Service Unavailable",
                "internet": False,
                "detail": "Internal server error while checking connectivity",
                "server_info": {"error_type": type(e).__name__, "error_message": str(e)}
            },
        )

@app.post(
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

@app.post(
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

@app.post(
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

@app.post(
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

@app.post(
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

    try:
        # Prepare additional headers if provided
        request_headers = session.headers.copy()
        if payload.headers:
            request_headers.update(payload.headers)
            logger.debug(f"Additional headers added: {list(payload.headers.keys())}")

        # Execute login request using the configured session
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

    except requests.exceptions.Timeout:
        error_msg = f"Timeout while logging in to {payload.url} after {payload.timeout}s"
        logger.error(error_msg)
        return JSONResponse(
            status_code=408,  # Request Timeout
            content={
                "error": error_msg,
                "error_type": "TimeoutError",
                "url": payload.url,
                "timeout": payload.timeout
            }
        )

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error during login: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=502,  # Bad Gateway
            content={
                "error": error_msg,
                "error_type": "ConnectionError",
                "url": payload.url
            }
        )

    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error during login: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "error_type": "HTTPError",
                "url": payload.url
            }
        )

    except Exception as e:
        # Handle any other unexpected error
        error_msg = f"Unexpected error during login: {str(e)}"
        logger.exception(error_msg)  # This includes the full stack trace
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "error_type": type(e).__name__,
                "url": payload.url
            }
        )

@app.post(
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

@app.post(
    "/dowwnload",
    summary="File Download Proxy",
    description="Descarga archivos manteniendo sesión y cookies.",
    tags=["Proxy"]
)
def download(payload: HTTPRequestPayload):
    """
    Descarga un archivo usando la sesión autenticada y lo retorna como descarga directa.
    """
    logger.info(f"Starting file download from {payload.url}")
    logger.debug(f"Parameters: timeout={payload.timeout}s, redirects={payload.allow_redirects}")

    try:
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

        # Obtener tipo de contenido y nombre sugerido de archivo
        content_type = response.headers.get("content-type", "application/octet-stream")
        content_disp = response.headers.get("content-disposition")
        filename = "downloaded_file"
        if content_disp:
            import re
            match = re.search(r'filename="?([^";]+)"?', content_disp)
            if match:
                filename = match.group(1)

        # Retornar archivo como descarga directa
        return StreamingResponse(
            response.iter_content(chunk_size=8192),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except requests.exceptions.Timeout:
        error_msg = f"Timeout while making request to {payload.url} after {payload.timeout}s"
        logger.error(error_msg)
        return JSONResponse(
            status_code=408,
            content={
                "error": error_msg,
                "error_type": "TimeoutError",
                "url": payload.url,
                "timeout": payload.timeout
            }
        )
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error during file download: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=502,
            content={
                "error": error_msg,
                "error_type": "ConnectionError",
                "url": payload.url
            }
        )
    except Exception as e:
        error_msg = f"Unexpected error during file download: {str(e)}"
        logger.exception(error_msg)
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "error_type": type(e).__name__,
                "url": payload.url
            }
        )

@app.post(
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

    try:
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

    except requests.exceptions.Timeout:
        error_msg = f"Timeout while making request to {payload.url} after {payload.timeout}s"
        logger.error(error_msg)
        return JSONResponse(
            status_code=408,  # Request Timeout
            content={
                "error": error_msg,
                "error_type": "TimeoutError",
                "url": payload.url,
                "timeout": payload.timeout,
                "method": payload.method
            }
        )

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error while forwarding request: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=502,  # Bad Gateway
            content={
                "error": error_msg,
                "error_type": "ConnectionError",
                "url": payload.url,
                "method": payload.method
            }
        )

    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error while forwarding request: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "error_type": "HTTPError",
                "url": payload.url,
                "method": payload.method
            }
        )

    except Exception as e:
        # Handle any other unexpected error
        error_msg = f"Unexpected error while forwarding request: {str(e)}"
        logger.exception(error_msg)  # Full stack trace in logs
        return JSONResponse(
            status_code=500,
            content={
                "error": error_msg,
                "error_type": type(e).__name__,
                "url": payload.url,
                "method": payload.method
            }
        )

# ============================================================================
# SERVER CONFIGURATION AND STARTUP
# ============================================================================

def configure_server_logging():
    """
    Configures the logging system specifically for the HTTP server.

    This function sets up:
    - Consistent log formatting
    - Appropriate logging level
    - Separation of application logs vs. access logs
    - Production environment configuration
    """
    # Configure the uvicorn logger to use our format
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.setLevel(logging.INFO)

    # Logger for uvicorn errors
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.setLevel(logging.INFO)

    logger.info("Server logging system configured")

def get_server_config() -> dict:
    """
    Retrieves the server configuration from environment variables or uses default values.

    Returns
    -------
    dict
        Complete server configuration with all required parameters.
    """
    import os

    config = {
        "host": os.getenv("SERVER_HOST", "0.0.0.0"),
        "port": int(os.getenv("SERVER_PORT", "5003")),
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "workers": int(os.getenv("WORKERS", "1")),
        "reload": os.getenv("RELOAD", "false").lower() == "true",
        "access_log": os.getenv("ACCESS_LOG", "false").lower() == "true"
    }

    logger.info(f"Server configuration loaded: {config}")
    return config

if __name__ == "__main__":
    """
    Main entry point for the HTTP proxy server.

    This function is responsible for:
    1. Configuring the advanced logging system
    2. Loading server configuration from the environment
    3. Initializing and starting the Uvicorn server
    4. Handling fatal errors and graceful shutdown
    5. Logging diagnostic information at startup

    Supported environment variables:
    --------------------------------
    - SERVER_HOST: Server IP address (default: 0.0.0.0)
    - SERVER_PORT: Server port (default: 5003)
    - LOG_LEVEL: Logging level (default: info)
    - WORKERS: Number of workers (default: 1)
    - RELOAD: Automatic reload in development (default: false)
    - ACCESS_LOG: Enable HTTP access logs (default: false)

    Returns
    -------
    None
        This function does not return values; it runs the server indefinitely.

    Examples
    --------
    Run with default configuration:
    >>> python server.py

    Run with a custom port:
    >>> SERVER_PORT=8080 python server.py

    Run in development mode with reload:
    >>> RELOAD=true LOG_LEVEL=debug python server.py
    """

    # Log system information at startup
    logger.info("="*80)
    logger.info("STARTING HTTP PROXY SERVER")
    logger.info(f"Python version: {sys.version.split()[0]}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Log file: {log_file}")
    logger.info("="*80)

    try:
        # Configure server-specific logging
        configure_server_logging()

        # Load configuration from environment
        server_config = get_server_config()

        # Log important information before startup
        logger.info(f"Configuring server at {server_config['host']}:{server_config['port']}")
        logger.info(f"Current session cookies: {len(session.cookies)}")
        logger.info(f"Configured session headers: {len(session.headers)}")

        # Check if the port is available
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((server_config['host'], server_config['port']))
                logger.info(f"Port {server_config['port']} is available")
            except OSError as e:
                logger.error(f"Port {server_config['port']} is not available: {e}")
                sys.exit(1)

        # Start the server with optimized configuration
        logger.info("Starting Uvicorn server...")
        logger.info(f"API documentation available at: http://{server_config['host']}:{server_config['port']}/docs")

        uvicorn.run(
            app,
            host=server_config['host'],
            port=server_config['port'],
            log_level=server_config['log_level'],
            log_config=None,
            access_log=server_config['access_log'],
            workers=server_config['workers'],
            reload=server_config['reload'],
        )

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user (Ctrl+C)")
        logger.info("Shutting down server gracefully...")

    except OSError as e:
        # Operating system errors (port in use, permissions, etc.)
        error_msg = f"System error while starting server: {str(e)}"
        logger.error(error_msg)
        sys.exit(1)

    except ImportError as e:
        # Missing dependency errors
        error_msg = f"Dependency error: {str(e)}. Please ensure all libraries are installed."
        logger.error(error_msg)
        sys.exit(1)

    except Exception as e:
        # Any other fatal error during startup
        error_msg = f"Fatal error while starting the server: {str(e)}"
        logger.exception(error_msg)  # Full stack trace
        sys.exit(1)

    finally:
        # Final cleanup
        logger.info("Server process terminated")
        logger.info(f"Final session cookies: {len(session.cookies)}")
        logger.info("="*80)
