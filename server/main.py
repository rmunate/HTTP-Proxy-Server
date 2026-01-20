from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    version="3.0.0",
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
