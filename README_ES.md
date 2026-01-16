# HTTP Proxy Server - Ejecutable para Windows

## 📋 Descripción

Este proyecto contiene un servidor HTTP proxy compilado como ejecutable para Windows que funciona completamente en segundo plano sin mostrar consola.

## ✨ Características

- ✅ **Ejecutable independiente**: No requiere Python instalado
- ✅ **Sin consola visible**: Funciona como servicio en segundo plano
- ✅ **Sesiones persistentes**: Mantiene cookies y autenticación automáticamente
- ✅ **API REST completa**: Endpoints para login, proxy y health check
- ✅ **Documentación integrada**: Swagger UI disponible en `/docs`
- ✅ **Logging detallado**: Logs automáticos en archivo `.log`
- ✅ **Tamaño optimizado**: Solo 11.4 MB con todas las dependencias

## 🚀 Uso Rápido

### Opción 1: Ejecutar directamente
```bash
# Ejecutar el servidor (sin consola)
HttpProxyServer.exe
```

## 🌐 Endpoints Disponibles

### 📊 Health Check
```http
GET http://localhost:5003/health
```

### 🔐 Login / Autenticación
```http
POST http://localhost:5003/login
Content-Type: application/json

{
  "url": "https://sistema.empresa.com/login",
  "method": "POST",
  "data": {
    "username": "usuario",
    "password": "contraseña"
  },
  "headers": {
    "Content-Type": "application/x-www-form-urlencoded"
  }
}
```

### � Logout / Terminación de Sesión
```http
POST http://localhost:5003/logout
```

### �🔄 Proxy / Reenvío de Peticiones
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

### 🛠️ Set Headers / Configurar Headers de Sesión
```http
POST http://localhost:5003/set-headers
Content-Type: application/json

{
  "X-Custom-Header": "ValorPersonalizado",
  "Authorization": "Bearer token123"
}
```
> Permite definir headers personalizados que se incluirán en todas las peticiones futuras del proxy. Útil para autenticaciones o configuraciones corporativas.

## 📚 Documentación Interactiva

Una vez que el servidor esté ejecutándose, accede a:

- **Swagger UI**: http://localhost:5003/docs
- **ReDoc**: http://localhost:5003/redoc
- **Health Check**: http://localhost:5003/health

## 🔧 Configuración Avanzada

### Variables de Entorno

Puedes configurar el servidor usando variables de entorno:

```bash
# Configurar host y puerto
set SERVER_HOST=0.0.0.0
set SERVER_PORT=8080

# Configurar nivel de logging
set LOG_LEVEL=debug

# Habilitar logs de acceso HTTP
set ACCESS_LOG=true

# Ejecutar servidor
HttpProxyServer.exe
```

### Archivo de Configuración

Crear archivo `.env` en la misma carpeta que el ejecutable:

```env
SERVER_HOST=0.0.0.0
SERVER_PORT=5003
LOG_LEVEL=info
ACCESS_LOG=false
RELOAD=false
WORKERS=1
```

## 📝 Logs y Debugging

### Ubicación de Logs
- **Archivo de log**: `HttpProxyServer.log` (misma carpeta que el .exe)

### Niveles de Log
- `debug`: Información muy detallada
- `info`: Información general (predeterminado)
- `warning`: Solo advertencias y errores
- `error`: Solo errores

### Ejemplo de Log
```
2026-01-15 20:49:00,123 [INFO] __main__ - Aplicación FastAPI inicializada correctamente
2026-01-15 20:49:00,124 [INFO] __main__ - Sesión HTTP configurada con User-Agent: Mozilla/5.0...
2026-01-15 20:49:01,456 [INFO] __main__ - Iniciando verificación de salud del servicio
2026-01-15 20:49:01,789 [INFO] __main__ - Verificación de salud exitosa - Internet disponible
```

### Detener el Servidor
1. **Administrador de Tareas**:
   - `Ctrl + Shift + Esc`
   - Buscar "HttpProxyServer.exe"
   - Terminar proceso

2. **Línea de comandos**:
   ```bash
   taskkill /f /im HttpProxyServer.exe
   ```

3. **PowerShell**:
   ```powershell
   Get-Process -Name "HttpProxyServer" | Stop-Process -Force
   ```

### Verificar si está Ejecutándose
```bash
# Verificar proceso
tasklist | findstr HttpProxyServer

# Verificar conectividad
curl http://localhost:5003/health
```

## 🔄 Workflow Típico de Uso

### 1. Autenticación
```bash
curl -X POST "http://localhost:5003/login" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://sistema.empresa.com/login",
    "method": "POST",
    "data": {
      "username": "mi_usuario",
      "password": "mi_contraseña"
    }
  }'
```

### 2. Realizar Peticiones Autenticadas
```bash
curl -X POST "http://localhost:5003/forward" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://sistema.empresa.com/api/datos",
    "method": "GET"
  }'
```

### 3. Logout (Opcional)
```bash
curl -X POST "http://localhost:5003/logout"
```

### 0. Configurar Headers Personalizados (opcional)
```bash
curl -X POST "http://localhost:5003/set-headers" \
  -H "Content-Type: application/json" \
  -d '{
    "X-Custom-Header": "ValorPersonalizado",
    "Authorization": "Bearer token123"
  }'
```

## 🚨 Solución de Problemas

### Puerto Ocupado
```
Error del sistema al iniciar servidor: [WinError 10048]
Solo se permite el uso de una dirección (protocolo/dirección de red/puerto) por cada socket
```

**Solución:**
1. Cambiar el puerto: `set SERVER_PORT=8080`
2. O terminar proceso existente: `taskkill /f /im HttpProxyServer.exe`

### Error de Permisos
```
Error del sistema al iniciar servidor: [WinError 5] Acceso denegado
```

**Solución:**
1. Ejecutar como Administrador
2. O usar puerto superior a 1024

### Sin Conectividad a Internet
```
{
  "status": "Service Unavailable",
  "internet": false,
  "detail": "Timeout al conectar con google.com"
}
```

**Solución:**
1. Verificar conexión a internet
2. Verificar configuración de proxy corporativo
3. Verificar firewall

## 🔐 Seguridad

- ✅ **SSL/TLS**: Soporte completo para HTTPS
- ✅ **Validación de entrada**: Pydantic V2 para validación robusta
- ✅ **Logging de auditoría**: Registro completo de todas las operaciones
- ✅ **Headers de seguridad**: User-Agent y headers corporativos
- ✅ **Timeouts**: Configurables para prevenir ataques de DoS

## 📞 Soporte

Para problemas o preguntas:
1. Revisar los logs en `HttpProxyServer.log`
2. Verificar la documentación en `/docs`
3. Contactar al desarrollador: Raul Mauricio Uñate Castro

## 📝 Desarrollar Nuevas Caracteristicas

1. Clonar el repositorio
```bash
git clone .....
cd http-proxy-server
```

2. Crear entorno virtual e instalar dependencias
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Modificar el código en `server.py`

---

**Versión**: 2.0.0
**Fecha**: 15 de Enero de 2026
**Compatible con**: Windows 10/11, Server 2016+