import os

SCRIPT_NAME = "main.py"
EXE_NAME = "HttpProxyServer"
VERSION = "3.0.0"
DESCRIPTION = "HTTP Proxy Server - Persistent session proxy server"
COMPANY = "Open Source"
COPYRIGHT = "© 2026 Raul Mauricio Uñate Castro"
ICON_FILE = os.path.join(os.path.dirname(__file__), "icon.ico")
VENV_NAME = "tmp_venv"
HIDDEN_IMPORTS = [
    "uvicorn.workers",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "httptools",
    "websockets",
    "pydantic.v1",
    "email_validator"
]
SOURCE_FOLDERS = [
    "middleware",
    "request",
    "response",
    "routes",
    "services"
]