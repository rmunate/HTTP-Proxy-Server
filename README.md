<div align="center">
  <img src="https://images.icon-icons.com/78/PNG/128/network_15177.png" alt="HTTP Proxy Logo" width="120" />
</div>

# HTTP Proxy Server

<div align="center">
<b>Your secure, flexible and professional gateway for managing HTTP/HTTPS traffic!</b>
</div>

---

## 📋 Overview

HTTP Proxy Server is an advanced solution to manage, audit, and control HTTP/HTTPS traffic, ideal for companies and developers. You can run it as a Windows service or as a Python script.

**Main features:**

- 🔒 Persistent and isolated sessions for each client
- ⚡ Full RESTful API: login, proxy, session management, headers and cookies
- 🛠️ Flexible configuration via `.env` file or environment variables
- 📑 Detailed activity logs
- 🧩 Interactive documentation (Swagger UI)

---

## 🚀 How to run the server?

### 🖥️ As an executable (Windows)
1. Place `HttpProxyServer.exe` in the desired folder and run:
   ```bash
   HttpProxyServer.exe
   ```
   The process runs in the background, with no visible console.

### 🐍 As a Python script (development)
1. Clone the repository and enter the folder:
   ```bash
   git clone <repo_url>
   cd http-proxy-server
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   python main.py
   ```

---

## ⚙️ Configuration

Configuration is flexible and follows this priority:
1. `.env` file (in the same folder as the executable/script)
2. Environment variables
3. Default values

**Example `.env`:**
```env
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=info
ACCESS_LOG=false
RELOAD=false
WORKERS=1
SESSION_TIMEOUT=600
CLEANUP_INTERVAL=300
```

**Equivalent environment variables:**
```bash
set SERVER_HOST=0.0.0.0
set SERVER_PORT=9000
set LOG_LEVEL=debug
set SESSION_TIMEOUT=1200
set CLEANUP_INTERVAL=600
set ACCESS_LOG=true
```

---

## 🌐 Main endpoints and use cases

> **Note:** After creating a session, you must send the `X-Session-ID` header in all requests.

### Health Check
`GET /health-check` — Checks server and connectivity status.

### Create session
`POST /subscribe` — Creates a unique session for the client.
Response:
```json
{
  "status": "OK",
  "session": { "session_id": "..." }
}
```

### Delete session
`POST /unsubscribe` — Deletes the session and clears cookies/headers.

### Set custom headers
`POST /set-headers` — Defines HTTP headers for the session.
```json
{
  "Authorization": "Bearer token123",
  "X-Custom-Header": "CustomValue"
}
```

### Get current headers
`POST /get-headers` — Returns the configured headers.

### Get current cookies
`POST /get-cookies` — Returns the session's active cookies.

### Full session info
`POST /get-session-info`

### HTTP/HTTPS proxy requests
`POST /forward` — Forwards any HTTP/HTTPS request using the active session.
```json
{
  "url": "https://api.company.com/data",
  "method": "GET",
  "headers": { "Accept": "application/json", "X-Session-ID": "abc123" }
}
```

### File download
`POST /dowwnload` — Downloads binary files while maintaining session and authentication.
```json
{
  "url": "https://files.company.com/download/file.zip",
  "method": "GET"
}
```

---

## 📝 Logs

- All events are logged in `HttpProxyServer.log`.
- Levels: debug, info, warning, error.
- Example:
  ```
  2026-01-15 20:49:00,123 [INFO] __main__ - Application initialized successfully
  2026-01-15 20:49:01,456 [INFO] __main__ - Starting service health check
  ```

---

## 🛑 How to stop the server?

- **Task Manager**: `Ctrl+Shift+Esc` → find `HttpProxyServer.exe` → end process
- **Command line**: `taskkill /f /im HttpProxyServer.exe`
- **PowerShell**: `Get-Process -Name "HttpProxyServer" | Stop-Process -Force`

---

## 🌀 Typical workflow example

1. Create session: `POST /subscribe`
2. Login to external system using `/forward`:
   ```bash
   curl -X POST "http://localhost:8000/forward" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://system.company.com/login",
       "method": "POST",
       "data": {
         "username": "my_user",
         "password": "my_password"
       },
       "headers": { "Content-Type": "application/x-www-form-urlencoded" }
     }'
   ```
3. Make authenticated requests: `POST /forward`
4. Download files: `POST /dowwnload`
5. Set custom headers: `POST /set-headers`
6. Logout: `POST /unsubscribe`

---

## 🛠️ Troubleshooting

- **Port in use**: Change the port in `.env` or stop the existing process.
- **Permissions**: Run as administrator or use ports >1024.
- **No internet**: Check network, corporate proxy, or firewall.

---

## 🔐 Security

- HTTPS support, robust validation, audit logging, security headers, configurable timeouts, and more.

---

## 📚 Interactive documentation

- [Swagger UI](http://localhost:5003/docs)
- [ReDoc](http://localhost:5003/redoc)
- [Health Check](http://localhost:5003/health-check)

---

**Developer:** Raul Mauricio Uñate Castro  
**Version:** 3.0.0  
**Date:** January 20, 2026
