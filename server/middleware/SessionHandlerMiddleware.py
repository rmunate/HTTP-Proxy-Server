"""
Session Handler Middleware
=========================

All-in-one middleware for automatic session management.
Contains complete session logic without external dependencies.

This middleware:
- Intercepts all HTTP requests
- Creates and validates sessions automatically
- Stores cookies and session data
- Detailed logging
- Adds custom headers
- Automatic cleanup of expired sessions

Author: Raul M. Uñate
"""

import time
import uuid
import logging
import asyncio
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logger specific for middleware
logger = logging.getLogger(__name__)

class SessionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Complete middleware for HTTP session management.
    
    Integrated functionalities:
    - In-memory session storage
    - Automatic session creation
    - Active session validation
    - Expired session cleanup
    - Detailed request logging
    - Custom headers
    - Periodic cleanup task
    """
    
    def __init__(self, app, session_timeout: int = 3600, cleanup_interval: int = 300):
        """
        Initialize middleware with internal session storage.
        
        Args:
            app: FastAPI application
            session_timeout: Session lifetime in seconds (default: 1 hour)
            cleanup_interval: Cleanup task interval in seconds (default: 5 minutes)
        """
        super().__init__(app)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
        self.cleanup_interval = cleanup_interval
        self._cleanup_task = None
        
        logger.info(f"SessionHandlerMiddleware initialized with timeout={session_timeout}s, cleanup={cleanup_interval}s")
        
        # Start automatic cleanup task
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the background cleanup task for expired sessions."""
        async def cleanup_expired_sessions():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    self._cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        # Start the cleanup task
        self._cleanup_task = asyncio.create_task(cleanup_expired_sessions())
        logger.info("Automatic session cleanup task started")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions from memory."""
        expired_sessions = []
        current_time = datetime.now()
        
        for session_id, session_data in self.sessions.items():
            last_activity = session_data["last_activity"]
            if current_time - last_activity > timedelta(seconds=self.session_timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"🗑️ Cleaned up {len(expired_sessions)} expired sessions")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each HTTP request - CORE of the middleware.
        
        Flow:
        1. Log incoming request
        2. Get/create session
        3. Validate authentication if needed
        4. Execute endpoint
        5. Update session
        6. Add headers and log response
        """
        start_time = time.time()
        client_ip = request.client.host
        method = request.method
        url = str(request.url)
        
        # === BEFORE REQUEST ===
        logger.info(f"🌐 {method} {url} from {client_ip}")
        
        # 1. Get or create session
        session_id = self._get_or_create_session(request)
        
        # 2. Validate authentication if required
        if self._requires_authentication(request.url.path):
            if not self._is_session_valid(session_id):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Invalid or expired session",
                        "session_id": session_id,
                        "message": "Please login again"
                    }
                )
        
        # 3. Add session data to request for endpoints to use
        request.state.session_id = session_id
        request.state.session_data = self.sessions.get(session_id)
        
        # === EXECUTE ENDPOINT ===
        try:
            response = await call_next(request)
            
            # === AFTER REQUEST ===
            process_time = time.time() - start_time
            
            # 4. Update session activity
            self._update_session_activity(session_id)
            
            # 5. Add informative headers
            response.headers["X-Session-ID"] = session_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            
            # 6. Log successful response
            logger.info(
                f"✅ {response.status_code} | "
                f"{process_time:.3f}s | "
                f"Session: {session_id[:8]}..."
            )
            
            return response
            
        except Exception as e:
            # === CENTRALIZED ERROR HANDLING ===
            process_time = time.time() - start_time
            
            # Determine error type and status code
            if "ConnectionError" in str(type(e)):
                status_code = 502  # Bad Gateway
                error_type = "ConnectionError"
            elif "Timeout" in str(type(e)):
                status_code = 408  # Request Timeout
                error_type = "TimeoutError"
            elif "HTTPError" in str(type(e)):
                status_code = 500
                error_type = "HTTPError"
            elif hasattr(e, 'status_code'):
                # Handle HTTPException from FastAPI
                status_code = e.status_code
                error_type = "HTTPException"
            else:
                status_code = 500
                error_type = type(e).__name__
            
            logger.error(
                f"❌ {error_type}: {str(e)} | "
                f"{process_time:.3f}s | "
                f"Session: {session_id[:8]}... | "
                f"Status: {status_code}"
            )
            
            # Build consistent error response
            error_response = JSONResponse(
                status_code=status_code,
                content={
                    "error": str(e),
                    "error_type": error_type,
                    "session_id": session_id,
                    "process_time": f"{process_time:.3f}s",
                    "timestamp": datetime.now().isoformat(),
                    "path": str(request.url.path),
                    "method": request.method
                }
            )
            
            # Add session headers even to error responses
            error_response.headers["X-Session-ID"] = session_id
            error_response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            
            return error_response
    
    # === INTERNAL SESSION METHODS ===
    
    def _get_or_create_session(self, request: Request) -> str:
        """Get existing session_id or create a new one."""
        # Search in cookies first
        session_id = request.cookies.get("session_id")
        
        # If not in cookies, search in headers
        if not session_id:
            session_id = request.headers.get("X-Session-ID")
        
        # If doesn't exist or is invalid, create new session
        if not session_id or not self._session_exists(session_id):
            session_id = self._create_session(
                client_ip=request.client.host,
                user_agent=request.headers.get("user-agent", "Unknown")
            )
            logger.info(f"🆕 New session: {session_id[:8]}...")
        else:
            logger.debug(f"📱 Existing session: {session_id[:8]}...")
        
        return session_id
    
    def _create_session(self, client_ip: str, user_agent: str = None) -> str:
        """Create a new session with initial data."""
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "is_authenticated": False,
            "user_data": {},
            "cookies": {},
            "request_count": 0
        }
        
        return session_id
    
    def _session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self.sessions
    
    def _is_session_valid(self, session_id: str) -> bool:
        """Check if a session exists and has not expired."""
        if not self._session_exists(session_id):
            return False
        
        session = self.sessions[session_id]
        last_activity = session["last_activity"]
        
        # Check expiration
        if datetime.now() - last_activity > timedelta(seconds=self.session_timeout):
            logger.info(f"🗑️ Expired session removed: {session_id[:8]}...")
            del self.sessions[session_id]
            return False
        
        return True
    
    def _update_session_activity(self, session_id: str):
        """Update last activity timestamp."""
        if self._session_exists(session_id):
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["request_count"] += 1
    
    def _requires_authentication(self, path: str) -> bool:
        """Determine if an endpoint requires authentication."""
        # Public routes that do NOT require authentication
        public_paths = [
            "/health", 
            "/docs", 
            "/openapi.json", 
            "/redoc",
            "/",
            "/my-session",  # To view session info without auth
            "/subscribe",   # To create sessions
            "/unsubscribe"  # To delete sessions (will be restricted in endpoint)
        ]
        
        return path not in public_paths
    
    # === PUBLIC METHODS FOR ENDPOINT USE ===
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Public method to get session data."""
        return self.sessions.get(session_id)
    
    def authenticate_session(self, session_id: str, user_data: Dict[str, Any]):
        """Mark a session as authenticated."""
        if self._session_exists(session_id):
            self.sessions[session_id]["is_authenticated"] = True
            self.sessions[session_id]["user_data"] = user_data
            logger.info(f"🔐 Session authenticated: {session_id[:8]}...")
    
    def logout_session(self, session_id: str):
        """Deauthenticate a session."""
        if self._session_exists(session_id):
            self.sessions[session_id]["is_authenticated"] = False
            self.sessions[session_id]["user_data"] = {}
            logger.info(f"🚪 Session logout: {session_id[:8]}...")
    
    def store_cookies(self, session_id: str, cookies: Dict[str, str]):
        """Store cookies in the session."""
        if self._session_exists(session_id):
            self.sessions[session_id]["cookies"].update(cookies)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics of active sessions."""
        total = len(self.sessions)
        authenticated = sum(1 for s in self.sessions.values() if s["is_authenticated"])
        
        return {
            "total_sessions": total,
            "authenticated_sessions": authenticated,
            "anonymous_sessions": total - authenticated,
            "session_timeout": self.session_timeout,
            "cleanup_interval": self.cleanup_interval
        }