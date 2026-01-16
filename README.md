# HTTP Proxy Server - Windows Executable

## 📋 Description

This project provides an HTTP proxy server compiled as a Windows executable that runs completely in the background with no visible console.

## ✨ Features

- ✅ **Standalone executable**: No Python installation required
- ✅ **No visible console**: Runs as a background service
- ✅ **Persistent sessions**: Automatically maintains cookies and authentication
- ✅ **Full REST API**: Endpoints for login, proxy, and health check
- ✅ **Integrated documentation**: Swagger UI available at `/docs`
- ✅ **Detailed logging**: Automatic logs in `.log` file
- ✅ **Optimized size**: Only 11.4 MB including all dependencies

## 🚀 Quick Start

### Option 1: Run directly
```bash
# Run the server (no console)
HttpProxyServer.exe
```

## 🌐 Available Endpoints


### 📊 Health Check
```http
GET http://localhost:5003/health
```

### 🔐 Login / Authentication
```http
POST http://localhost:5003/login
Content-Type: application/json

{
  "url": "https://sistema.empresa.com/login",
  "method": "POST",
  "data": {
    "username": "user",
    "password": "password"
  },
  "headers": {
    "Content-Type": "application/x-www-form-urlencoded"
  }
}
```

### � Logout / Session Termination
```http
POST http://localhost:5003/logout
```

### �🔄 Proxy / Request Forwarding
```http
POST http://localhost:5003/forward
Content-Type: application/json

{
  "url": "https://api.empresa.com/datos",
  "method": "GET",
  "headers": {
    "Accept": "application/json"
  }
}
```

### 🛠️ Set Headers / Set Session Headers
```http
POST http://localhost:5003/set-headers
Content-Type: application/json

{
  "X-Custom-Header": "CustomValue",
  "Authorization": "Bearer token123"
}
```
> Allows you to define custom headers that will be included in all future proxy requests. Useful for authentication or corporate header requirements.

### 🗂️ Get Session Headers
```http
POST http://localhost:5003/get-headers
```
Returns all headers currently configured in the proxy HTTP session.

### 🍪 Get Session Cookies
```http
POST http://localhost:5003/get-cookies
```
Returns all cookies stored in the current proxy session.

### 📋 Get Detailed Session Info
```http
POST http://localhost:5003/get-session-info
```
Returns complete information about the current HTTP session, including headers, cookies, and SSL configuration.

---
#### 🆕 New method: `/set-headers`

This endpoint allows you to set **custom HTTP headers** that will be automatically included in all future session requests. It's ideal for adding authentication tokens, corporate headers, or any information that should persist in proxied requests.

**Usage example:**
```http
POST /set-headers
{
  "Authorization": "Bearer token123",
  "X-Custom-Header": "CustomValue"
}
```

**Benefits:**
- Centralizes authentication and header management.
- Facilitates integration with enterprise APIs.
- Allows header changes without restarting the session.

## 📚 Interactive Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:5003/docs
- **ReDoc**: http://localhost:5003/redoc
- **Health Check**: http://localhost:5003/health

## 🔧 Advanced Configuration

### Environment Variables

You can configure the server using environment variables:

```bash
# Set host and port
set SERVER_HOST=0.0.0.0
set SERVER_PORT=8080

# Set logging level
set LOG_LEVEL=debug

# Enable HTTP access logs
set ACCESS_LOG=true

# Run server
HttpProxyServer.exe
```

### Configuration File

Create a `.env` file in the same folder as the executable:

```env
SERVER_HOST=0.0.0.0
SERVER_PORT=5003
LOG_LEVEL=info
ACCESS_LOG=false
RELOAD=false
WORKERS=1
```

## 📝 Logs and Debugging

### Log Location
- **Log file**: `HttpProxyServer.log` (same folder as the .exe)

### Log Levels
- `debug`: Very detailed information
- `info`: General information (default)
- `warning`: Only warnings and errors
- `error`: Errors only

### Log Example
```
2026-01-15 20:49:00,123 [INFO] __main__ - FastAPI application initialized successfully
2026-01-15 20:49:00,124 [INFO] __main__ - HTTP session configured with User-Agent: Mozilla/5.0...
2026-01-15 20:49:01,456 [INFO] __main__ - Starting service health check
2026-01-15 20:49:01,789 [INFO] __main__ - Health check successful - Internet available
```

### Stopping the Server
1. **Task Manager**:
   - `Ctrl + Shift + Esc`
   - Find "HttpProxyServer.exe"
   - End process

2. **Command line**:
   ```bash
   taskkill /f /im HttpProxyServer.exe
   ```

3. **PowerShell**:
   ```powershell
   Get-Process -Name "HttpProxyServer" | Stop-Process -Force
   ```

### Check if Running
```bash
# Check process
tasklist | findstr HttpProxyServer

# Check connectivity
curl http://localhost:5003/health
```

## 🔄 Typical Workflow

### 1. Authentication
```bash
curl -X POST "http://localhost:5003/login" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://sistema.empresa.com/login",
    "method": "POST",
    "data": {
      "username": "my_user",
      "password": "my_password"
    }
  }'
```

### 2. Make Authenticated Requests
```bash
curl -X POST "http://localhost:5003/forward" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://sistema.empresa.com/api/datos",
    "method": "GET"
  }'
```

### 0. Set Custom Headers (optional)
```bash
curl -X POST "http://localhost:5003/set-headers" \
  -H "Content-Type: application/json" \
  -d '{
    "X-Custom-Header": "CustomValue",
    "Authorization": "Bearer token123"
  }'
```

### 3. Logout (Optional)
```bash
curl -X POST "http://localhost:5003/logout"
```

## 🚨 Troubleshooting

### Port Already in Use
```
System error when starting server: [WinError 10048]
Only one usage of each socket address (protocol/network address/port) is normally permitted
```

**Solution:**
1. Change the port: `set SERVER_PORT=8080`
2. Or terminate the existing process: `taskkill /f /im HttpProxyServer.exe`

### Permission Error
```
System error when starting server: [WinError 5] Access is denied
```

**Solution:**
1. Run as Administrator
2. Or use a port above 1024

### No Internet Connectivity
```
{
  "status": "Service Unavailable",
  "internet": false,
  "detail": "Timeout connecting to google.com"
}
```

**Solution:**
1. Check your internet connection
2. Check corporate proxy configuration
3. Check firewall

## 🔐 Security

- ✅ **SSL/TLS**: Full HTTPS support
- ✅ **Input validation**: Robust validation with Pydantic V2
- ✅ **Audit logging**: Complete record of all operations
- ✅ **Security headers**: User-Agent and corporate headers
- ✅ **Timeouts**: Configurable to prevent DoS attacks

## 📞 Support

For issues or questions:
1. Check the logs in `HttpProxyServer.log`
2. Review the documentation at `/docs`
3. Contact the developer: Raul Mauricio Uñate Castro

## 📝 Developing New Features

1. Clone the repository
```bash
git clone .....
cd http-proxy-server
```

2. Create a virtual environment and install dependencies
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Modify the code in `server.py`

---

**Version**: 2.0.0  
**Date**: January 15, 2026  
**Compatible with**: Windows 10/11, Server 2016+