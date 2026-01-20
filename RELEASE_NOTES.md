# 🚀 HTTP Proxy Server - Release Notes

## Version 3.0.0 - Enhanced Session Management
**Release Date:** January 20, 2026

---

### 📋 What is HTTP Proxy Server?

A **standalone Windows executable** that provides an HTTP proxy server with persistent session management, designed to act as a bridge between applications and external systems requiring authentication.

### 🎯 Key Features

- **🏢 Enterprise Ready**: Designed for corporate environments with proxy support
- **🔐 Advanced Session Management**: Subscribe/unsubscribe endpoints with automatic middleware
- **📺 Flexible Configuration**: .env files and environment variables support
- **🧙 Automatic Cleanup**: Expired session removal with configurable intervals
- **🛡️ Centralized Error Handling**: Consistent error management across all endpoints
- **📝 Session Management**: Automatic cookie and authentication handling
- **📦 Zero Dependencies**: Single 11.4MB executable, no Python installation required
- **🌐 REST API**: Complete FastAPI-based endpoints with Swagger documentation
- **📊 Health Monitoring**: Built-in connectivity and service health checks
- **📝 Audit Logging**: Comprehensive request/response logging for compliance

### 🛡️ Security & Reliability

- ✅ **SSL/TLS Support**: Full HTTPS compatibility
- ✅ **Input Validation**: Robust Pydantic V2 validation
- ✅ **Background Service**: Runs silently without console window
- ✅ **Timeout Protection**: Configurable timeouts prevent hanging requests
- ✅ **Error Handling**: Graceful error management with detailed logging

### 🌐 API Endpoints


| Endpoint              | Method | Purpose                                         |
|-----------------------|--------|------------------------------------------------|
| `/health`             | GET    | Service and connectivity health check           |
| `/subscribe`          | POST   | Create new personalized session                 |
| `/unsubscribe/{id}`   | DELETE | Remove specific session from system            |
| `/login`              | POST   | Authentication and session initialization       |
| `/logout`             | POST   | Session termination and cleanup                 |
| `/forward`            | POST   | HTTP request proxy with session persistence     |
| `/dowwnload`          | POST   | File download proxy (direct binary stream)      |
| `/set-headers`        | POST   | Set custom headers for all session requests     |
| `/get-headers`        | POST   | Get all current session headers                 |
| `/get-cookies`        | POST   | Get all current session cookies                 |
| `/get-session-info`   | POST   | Get detailed session information                |
| `/docs`               | GET    | Interactive Swagger API documentation           |

### 🔧 Configuration Options

- **.env File Support**: Automatic configuration loading from .env files
- **Environment Variables**: `SERVER_HOST`, `SERVER_PORT`, `LOG_LEVEL`, `SESSION_TIMEOUT`, `CLEANUP_INTERVAL`
- **Configuration Priority**: .env file > environment variables > defaults
- **Flexible Deployment**: Can run on any port, any interface
- **Production Ready**: Optimized for Windows Server environments

### 🚀 Quick Start

1. **Download** `HttpProxyServer.exe`
2. **Run** the executable (no installation required)
3. **Access** documentation at `http://localhost:8000/docs`
4. **Use** REST API for authentication and proxying

### 💼 Use Cases

- **Web Scraping**: Maintain authenticated sessions across requests
- **API Integration**: Bridge between systems requiring different authentication
- **Legacy System Access**: Modern REST interface for older authentication systems
- **Development & Testing**: Local proxy for development environments
- **Corporate Applications**: Navigate through corporate proxy requirements


### 🆕 What's New in v3.0.0

- **New Session Management**: Subscribe/unsubscribe endpoints for advanced session control
- **Middleware Architecture**: Complete rewrite using centralized middleware approach
- **Automatic Session Cleanup**: Configurable background cleanup of expired sessions
- **Enhanced Configuration**: .env file support with priority-based configuration loading
- **Centralized Error Handling**: Consistent error responses across all endpoints
- **Improved Logging**: Enhanced logging with session tracking and performance metrics
- **Better Session Validation**: Automatic session validation and authentication checks
- **Default Port Change**: Now defaults to port 8000 (was 5003)

**New Subscribe Endpoint:**
```http
POST http://localhost:8000/subscribe
Content-Type: application/json

{
  "user_data": {
    "username": "user123",
    "department": "IT"
  }
}
```

**New Unsubscribe Endpoint:**
```http
DELETE http://localhost:8000/unsubscribe/{session_id}
```

### 📞 Support & Documentation

- **Full Documentation**: Available at `/docs` when server is running
- **Health Check**: Monitor service status via `/health` endpoint
- **Logging**: Automatic logs in `HttpProxyServer.log`
- **Author**: Raul Mauricio Uñate Castro

### 🏷️ Technical Specifications

- **Framework**: FastAPI 0.100+ with advanced middleware
- **Session Management**: In-memory with automatic cleanup
- **Configuration**: .env files + environment variables + defaults
- **Architecture**: Centralized middleware approach
- **Platform**: Windows 10/11, Windows Server 2016+
- **Size**: 11.4 MB (includes all dependencies)
- **Memory**: ~50MB runtime footprint
- **Language**: Python 3.12 (compiled to native executable)
