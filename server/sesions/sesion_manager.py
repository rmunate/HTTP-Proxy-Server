
Centrally manages user sessions.
Stores session information, cookies, and authentication state.

Author: Raul M. Uñate
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Centralized HTTP session manager.
    
    Features:
    - Create and delete sessions
    - Store cookies and session data
    - Validate active sessions
    - Clean up expired sessions
    """
    
    def __init__(self, session_timeout: int = 600):
        """
        Initializes the session manager.
        
        Args:
            session_timeout: Session lifetime in seconds (default: 10 minutes)
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = session_timeout
        logger.info(f"SessionManager initialized with timeout of {session_timeout}s")
    
    def create_session(self, client_ip: str, user_agent: str = None) -> str:
        """
        Creates a new session and returns the session_id.
        
        Args:
            client_ip: Client's IP address
            user_agent: User-Agent of the browser/client
            
        Returns:
            str: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
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
        
        self.sessions[session_id] = session_data
        logger.info(f"New session created: {session_id[:8]}... for IP {client_ip}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets the data of a specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with session data or None if it doesn't exist
        """
        return self.sessions.get(session_id)
    
    def session_exists(self, session_id: str) -> bool:
        """
        Verifies if a session exists.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if the session exists
        """
        return session_id in self.sessions
    
    def is_session_valid(self, session_id: str) -> bool:
        """
        Verifies if a session exists and has not expired.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if the session is valid
        """
        if not self.session_exists(session_id):
            return False
        
        session = self.sessions[session_id]
        last_activity = session["last_activity"]
        
        # Check if the session has expired
        if datetime.now() - last_activity > timedelta(seconds=self.session_timeout):
            logger.info(f"Expired session deleted: {session_id[:8]}...")
            self.delete_session(session_id)
            return False
        
        return True
    
    def update_last_activity(self, session_id: str):
        """
        Updates the last activity timestamp of a session.
        
        Args:
            session_id: Session ID
        """
        if self.session_exists(session_id):
            self.sessions[session_id]["last_activity"] = datetime.now()
            self.sessions[session_id]["request_count"] += 1
    
    def authenticate_session(self, session_id: str, user_data: Dict[str, Any]):
        """
        Marks a session as authenticated and stores user data.
        
        Args:
            session_id: Session ID
            user_data: Authenticated user data
        """
        if self.session_exists(session_id):
            self.sessions[session_id]["is_authenticated"] = True
            self.sessions[session_id]["user_data"] = user_data
            logger.info(f"Session authenticated: {session_id[:8]}...")
    
    def logout_session(self, session_id: str):
        """
        Marks a session as not authenticated.
        
        Args:
            session_id: Session ID
        """
        if self.session_exists(session_id):
            self.sessions[session_id]["is_authenticated"] = False
            self.sessions[session_id]["user_data"] = {}
            logger.info(f"Session logged out: {session_id[:8]}...")
    
    def delete_session(self, session_id: str):
        """
        Completely deletes a session.
        
        Args:
            session_id: Session ID
        """
        if self.session_exists(session_id):
            del self.sessions[session_id]
            logger.info(f"Session deleted: {session_id[:8]}...")
    
    def store_cookies(self, session_id: str, cookies: Dict[str, str]):
        """
        Stores cookies in the session.
        
        Args:
            session_id: Session ID
            cookies: Cookie dictionary
        """
        if self.session_exists(session_id):
            self.sessions[session_id]["cookies"].update(cookies)
    
    def get_cookies(self, session_id: str) -> Dict[str, str]:
        """
        Gets the cookies stored in a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with cookies or empty dictionary
        """
        session = self.get_session(session_id)
        return session.get("cookies", {}) if session else {}
    
    def cleanup_expired_sessions(self):
        """
        Automatically cleans up expired sessions.
        """
        expired_sessions = []
        current_time = datetime.now()
        
        for session_id, session_data in self.sessions.items():
            last_activity = session_data["last_activity"]
            if current_time - last_activity > timedelta(seconds=self.session_timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Gets statistics of active sessions.
        
        Returns:
            Dict with session statistics
        """
        total_sessions = len(self.sessions)
        authenticated_sessions = sum(1 for s in self.sessions.values() if s["is_authenticated"])
        
        return {
            "total_sessions": total_sessions,
            "authenticated_sessions": authenticated_sessions,
            "anonymous_sessions": total_sessions - authenticated_sessions,
            "session_timeout": self.session_timeout
        }
class SessionManager:

    def __init__(self):
        self.sessions = {}

    def 
