# HTTP Proxy Server - Ejecutable para Windows

## 📋 Descripción

Este proyecto contiene un servidor HTTP proxy compilado como ejecutable para Windows que funciona completamente en segundo plano sin mostrar consola.

## ✨ Características

- ✅ **Ejecutable independiente**: No requiere Python instalado
- ✅ **Sin consola visible**: Funciona como servicio en segundo plano
- ✅ **Sesiones persistentes**: Mantiene cookies y autenticación automáticamente
- ✅ **API REST completa**: Endpoints para login, proxy y health check
- ✅ **Gestión avanzada de sesiones**: Subscribe/unsubscribe con middleware automático
- ✅ **Configuración flexible**: Archivos .env y variables de entorno
- ✅ **Limpieza automática**: Eliminación automática de sesiones expiradas
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
<<<<<<< HEAD
GET http://localhost:5003/health
```

### 🔐 Login / Autenticación
```http
POST http://localhost:5003/login
=======
GET http://localhost:8000/health
```

### 🔗 Subscribe / Crear Sesión
```http
POST http://localhost:8000/subscribe
Content-Type: application/json

{
  "user_data": {
    "username": "usuario_opcional",
    "department": "ventas"
  }
}
```
> Crea una nueva sesión personalizada. El parámetro `user_data` es opcional y permite almacenar información adicional del usuario.

### 🚫 Unsubscribe / Eliminar Sesión
```http
DELETE http://localhost:8000/unsubscribe/{session_id}
```
> Elimina una sesión específica del sistema. Útil para limpieza manual o logout forzado.

### 🔐 Login / Autenticación
```http
POST http://localhost:8000/login
>>>>>>> cc3bf0e (add sessions, env, routes to subscribe and unsubscribe)
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

### 📤 Logout / Terminación de Sesión
```http
POST http://localhost:8000/logout
```

### 🔄 Proxy / Reenvío de Peticiones
```http
POST http://localhost:8000/forward
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
POST http://localhost:8000/set-headers
Content-Type: application/json

{
  "X-Custom-Header": "ValorPersonalizado",
  "Authorization": "Bearer token123"
}
```
> Permite definir headers personalizados que se incluirán en todas las peticiones futuras del proxy. Útil para autenticaciones o configuraciones corporativas.

### 🗂️ Obtener Headers de Sesión
```http
POST http://localhost:8000/get-headers
```
Devuelve todos los headers actualmente configurados en la sesión HTTP del proxy.

### 🍪 Obtener Cookies de Sesión
```http
POST http://localhost:8000/get-cookies
```
Devuelve todas las cookies almacenadas en la sesión actual del proxy.


### 📥 Descarga de Archivos
```http
POST http://localhost:8000/dowwnload
Content-Type: application/json

{
  "url": "https://files.company.com/download/file.zip",
  "method": "GET",
  "headers": {"Accept": "application/octet-stream"}
}
```
Devuelve el archivo solicitado como descarga directa (flujo binario). Usa este endpoint para descargar documentos, imágenes o cualquier tipo de archivo manteniendo la sesión y autenticación.

**Ejemplo usando curl:**
```bash
curl -X POST "http://localhost:5003/dowwnload" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://files.company.com/download/file.zip",
    "method": "GET"
  }' --output archivo.zip
```

---
#### 🆕 Nuevo método: `/set-headers`

Este endpoint permite establecer **headers HTTP personalizados** que serán incluidos automáticamente en todas las solicitudes futuras de la sesión. Es ideal para agregar tokens de autenticación, cabeceras corporativas o cualquier información que deba persistir en las peticiones proxificadas.

**Ejemplo de uso:**
```http
POST /set-headers
{
  "Authorization": "Bearer token123",
  "X-Custom-Header": "ValorPersonalizado"
}
```

**Ventajas:**
- Centraliza la gestión de autenticación y cabeceras.
- Facilita la integración con APIs empresariales.
- Permite modificar cabeceras sin reiniciar la sesión.

## 📚 Documentación Interactiva

Una vez que el servidor esté ejecutándose, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Configuración Avanzada

### Configuración con Archivo .env

Crea un archivo `.env` en la misma carpeta que el ejecutable para configuración automática:

```env
# Configuración del servidor
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=info
RELOAD=false
WORKERS=1
ACCESS_LOG=false

# Configuración de sesiones
SESSION_TIMEOUT=600
CLEANUP_INTERVAL=300
```

### Variables de Entorno

También puedes configurar el servidor usando variables de entorno:

```bash
# Configurar host y puerto
set SERVER_HOST=0.0.0.0
set SERVER_PORT=9000

# Configurar nivel de logging
set LOG_LEVEL=debug

# Configurar sesiones
set SESSION_TIMEOUT=1200
set CLEANUP_INTERVAL=600

# Habilitar logs de acceso HTTP
set ACCESS_LOG=true

# Ejecutar servidor
HttpProxyServer.exe
```

### Prioridad de Configuración

1. **Archivo .env** (mayor prioridad)
2. **Variables de entorno**
3. **Valores por defecto**

### Archivo de Configuración

Crear archivo `.env` en la misma carpeta que el ejecutable:

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
curl http://localhost:8000/health
```


### 🌀 Workflow Típico de Uso

#### 0. Crear Sesión (Nuevo)
```bash
curl -X POST "http://localhost:8000/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "user_data": {
      "username": "usuario_corporativo",
      "department": "IT"
    }
  }'
```

#### 1. Autenticación
```bash
curl -X POST "http://localhost:8000/login" \
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

#### 2. Realizar Peticiones Autenticadas
```bash
curl -X POST "http://localhost:8000/forward" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://sistema.empresa.com/api/datos",
    "method": "GET"
  }'
```

#### 3. Descargar Archivos (NUEVO)
```bash
curl -X POST "http://localhost:8000/dowwnload" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://files.company.com/download/file.zip",
    "method": "GET"
  }' --output archivo.zip
```

#### 0. Configurar Headers Personalizados (opcional)
```bash
curl -X POST "http://localhost:8000/set-headers" \
  -H "Content-Type: application/json" \
  -d '{
    "X-Custom-Header": "ValorPersonalizado",
    "Authorization": "Bearer token123"
  }'
```

#### 4. Logout (Opcional)
```bash
curl -X POST "http://localhost:8000/logout"
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

**Versión**: 3.0.0
**Fecha**: 20 de Enero de 2026
**Compatible con**: Windows 10/11, Server 2016+