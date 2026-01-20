from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import configuration
from config.settings import config

# Import only the middleware (no longer need SessionManager)
from middleware.SessionHandlerMiddleware import SessionHandlerMiddleware
from routes.api import router

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
                   - ✅ Automatic session management via middleware
                   - ✅ Session subscribe/unsubscribe endpoints
                   - ✅ Automatic cleanup of expired sessions
                """,
    version="3.0.0",
    contact={
        "name": "Raul M. Uñate",
        "email": "raulmauriciounate@gmail.com",
    },
    license_info={
        "name": "Raul M. Uñate",
    },
)

# === MIDDLEWARE CONFIGURATION ===
# IMPORTANT: Order matters - middlewares execute in reverse order

# 1. Session Handler (configured via .env or environment variables)
app.add_middleware(
    SessionHandlerMiddleware, 
    session_timeout=config.get('session_timeout'),
    cleanup_interval=config.get('cleanup_interval')
)

# 2. CORS (executes after session handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ROUTER INCLUSION ===
app.include_router(router)