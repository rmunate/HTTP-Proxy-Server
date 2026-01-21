import sys
from datetime import datetime
import urllib3
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.session_middleware import SessionMiddleware
from routes.api import proxy_router
from services.env import Env
from services.log import Log
from services.port import Port

# Disable insecure request warnings from urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize FastAPI application with metadata and documentation.
app = FastAPI(
    title="HTTP Proxy Server",
    description=(
        "HTTP proxy server that maintains persistent sessions and provides "
        "endpoints for authentication and request forwarding.\n\n"
        "Features:\n"
        "- ✅ Automatically maintains session cookies\n"
        "- ✅ Internet connectivity health check\n"
        "- ✅ Transparent HTTP/HTTPS request proxy\n"
        "- ✅ Detailed logging of all operations\n"
        "- ✅ Robust input data validation"
    ),
    version="3.0.0",
    contact={
        "name": "Raul M. Uñate",
        "email": "raulmauriciounate@gmail.com",
    },
    license_info={
        "name": "Raul M. Uñate",
    },
    openapi_tags=[
        {"name": "System", "description": "Endpoints for system health and status checks."},
        {"name": "Session", "description": "Endpoints for managing HTTP session headers and cookies."},
        {"name": "Authentication", "description": "Endpoints for user authentication and session management."},
        {"name": "Proxy", "description": "Endpoints for forwarding HTTP requests and downloading files."}
    ]
)

# Add CORS middleware to allow requests from any origin.
# This is important for web applications consuming this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware
)

app.include_router(
    proxy_router
)

if __name__ == "__main__":

    try:

        # Load server configuration from environment variables
        host = Env.get("SERVER_HOST", "0.0.0.0")
        port = int(Env.get("SERVER_PORT", 5003))
        log_level = Env.get("LOG_LEVEL", "info").lower()
        access_log = Env.get("ACCESS_LOG", "true").lower() == "true"
        workers = int(Env.get("WORKERS", 1))
        reload = Env.get("RELOAD", "false").lower() == "true"

        # Check if the specified port is available
        if not Port.isAvailable(host=host, port=port):
            Log.error(f"Port {port} is already in use. Please free the port and try again.")
            sys.exit(1)

        # Start the Uvicorn server with the specified configuration
        Log.info("Starting HTTP Proxy Server...")
        Log.info(f"API documentation available at: http://localhost:{port}/docs")

        # Server configuration dictionary
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            log_config=None,
            access_log=access_log,
            workers=workers,
            reload=reload,
        )

    except KeyboardInterrupt:
        # Keyboard interrupt during startup
        Log.info("Shutdown requested by user (Ctrl+C)")
        Log.info("Shutting down server gracefully...")

    except OSError as e:
        # Operating system errors (port in use, permissions, etc.)
        error_msg = f"System error while starting server: {str(e)}"
        Log.error(error_msg)
        sys.exit(1)

    except ImportError as e:
        # Missing dependency errors
        error_msg = f"Dependency error: {str(e)}. Please ensure all libraries are installed."
        Log.error(error_msg)
        sys.exit(1)

    except Exception as e:
        # Any other fatal error during startup
        error_msg = f"Fatal error while starting the server: {str(e)}"
        Log.error(error_msg)  # Full stack trace
        sys.exit(1)

    finally:
        # Final cleanup
        Log.info("Server process terminated at: " + str(datetime.now()))