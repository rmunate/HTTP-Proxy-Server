from datetime import datetime, timedelta
from typing import Any, Dict
import uuid
import requests

class SessionManager:

    _instance = None
    _sessions: Dict[str, Dict[str, Any]] = {}
    _session_timeout: int = 600

    def __new__(cls, session_timeout: int = 600) -> "SessionManager":
        """
        Create or return the singleton instance of SessionManager.

        Parameters
        ----------
        session_timeout : int, optional
            Timeout in seconds for session expiration.

        Returns
        -------
        SessionManager
            Singleton instance of SessionManager.
        """
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._session_timeout = session_timeout
        return cls._instance

    def __init__(self, session_timeout: int = 600) -> None:
        """
        Initialize the SessionManager instance.

        Parameters
        ----------
        session_timeout : int, optional
            Timeout in seconds for session expiration.

        Returns
        -------
        None
            This method does not return a value.
        """
        # Only initializes the timeout the first time
        pass

    def createSession(
        self,
        client_ip: str,
        user_agent: str | None = None
    ) -> str:
        """
        Create a new session and return the session ID.

        Parameters
        ----------
        client_ip : str
            IP address of the client.
        user_agent : str or None, optional
            User-Agent string of the browser or client.

        Returns
        -------
        str
            Unique session identifier.
        """
        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Create a new requests.Session instance
        session = requests.Session()
        session.verify = False

        # Initialize session data with default values
        session_data = {
            "session_id": session_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "request_count": 0,
            "instance" : session
        }

        # Store the session in the sessions dictionary
        self._sessions[session_id] = session_data
        return session_id

    def getSession(
        self,
        session_id: str
    ) -> dict[str, Any] | None:
        """
        Retrieve the data of a specific session.

        Parameters
        ----------
        session_id : str
            Unique identifier for the session.

        Returns
        -------
        dict[str, Any] or None
            Dictionary with session data if found, otherwise None.
        """
        # Return session data if it exists, otherwise None
        return self._sessions.get(session_id)

    def getSessionInstance(
        self,
        session_id: str
    ) -> requests.Session:
        """
        Retrieve the requests.Session instance for a session.

        Parameters
        ----------
        session_id : str
            Unique identifier for the session.

        Returns
        -------
        requests.Session
            The requests.Session instance associated with the session.

        Raises
        ------
        ValueError
            If the session is not found.
        """
        # Get the session dictionary for the given session_id
        session = self.getSession(session_id)
        if not session or "instance" not in session or not session["instance"]:
            error_msg = "Session not found."
            raise ValueError(error_msg)
        return session["instance"]

    def sessionExists(
        self,
        session_id: str
    ) -> bool:
        """
        Check if a session exists.

        Parameters
        ----------
        session_id : str
            Session ID.

        Returns
        -------
        bool
            True if the session exists, otherwise False.
        """
        # Return True if the session ID is present in the sessions dictionary
        return session_id in self._sessions

    def isSessionValid(
        self,
        session_id: str
    ) -> bool:
        """
        Check if a session exists and is not expired.

        Parameters
        ----------
        session_id : str
            Session ID.

        Returns
        -------
        bool
            True if the session exists and is not expired, otherwise False.
        """
        # Verify session existence
        if not self.sessionExists(session_id):
            return False

        session = self._sessions[session_id]
        last_activity = session["last_activity"]

        # Check if the session has expired
        if datetime.now() - last_activity > timedelta(seconds=self._session_timeout):
            self.deleteSession(session_id)
            return False
        return True

    def updateLastActivity(
        self,
        session_id: str
    ) -> None:
        """
        Update the last activity timestamp and increment request count.

        Parameters
        ----------
        session_id : str
            Session ID.

        Returns
        -------
        None
            This method does not return a value.
        """
        # Update last activity and increment request count if session exists
        if self.sessionExists(session_id):
            self._sessions[session_id]["last_activity"] = datetime.now()
            self._sessions[session_id]["request_count"] += 1

    def deleteSession(
        self,
        session_id: str
    ) -> None:
        """
        Delete a session completely.

        Parameters
        ----------
        session_id : str
            Session ID to be deleted.

        Returns
        -------
        None
            This method does not return a value.
        """
        # Remove the session if it exists
        if self.sessionExists(session_id):
            self._sessions[session_id]["instance"].close()
            del self._sessions[session_id]

    def cleanupExpiredSessions(self) -> None:
        """
        Remove expired sessions from the session store.

        Iterates through all sessions and deletes those whose last activity
        exceeds the session timeout.

        Returns
        -------
        None
            This method does not return a value.
        """
        expired_sessions = []
        current_time = datetime.now()
        for session_id, session_data in self._sessions.items():
            last_activity = session_data["last_activity"]
            if current_time - last_activity > timedelta(seconds=self._session_timeout):
                expired_sessions.append(session_id)
        for session_id in expired_sessions:
            self.deleteSession(session_id)

    def getSessionStats(self) -> Dict[str, Any]:
        """
        Retrieve statistics of active sessions.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing the total number of sessions, session timeout,
            and session details.
        """
        # Calculate the total number of active sessions
        total_sessions = len(self._sessions)
        return {
            "total_sessions": total_sessions,
            "session_timeout": self._session_timeout,
            "sessions": self._sessions,
        }