
# Servidor HTTP Proxy

## 📋 Descripción General

Este proyecto implementa un servidor HTTP Proxy avanzado, diseñado para ejecutarse como servicio en Windows (o como script Python), permitiendo la gestión de sesiones persistentes, autenticación, reenvío de peticiones HTTP/HTTPS, descarga de archivos y configuración dinámica de cabeceras y cookies.

- **API REST completa**: expone endpoints para login, proxy, gestión de sesiones, headers y cookies.
- **Sesiones persistentes**: cada cliente puede crear y gestionar su propia sesión aislada.
- **Configuración flexible**: soporta archivo `.env` y variables de entorno.
- **Logs detallados**: registra toda la actividad en un archivo `.log`.
- **Documentación interactiva**: Swagger UI en `/docs`.

---

## 🚀 Cómo Ejecutar el Servidor

### 1. Como ejecutable (Windows)
Coloca el archivo `HttpProxyServer.exe` en la carpeta deseada y ejecútalo:
```bash
HttpProxyServer.exe



<div align="center">
  <img src="https://images.icon-icons.com/78/PNG/128/network_15177.png" alt="Logo HTTP Proxy" width="120" />
</div>

# HTTP Proxy Server

<div align="center">
<b>¡Tu puerta de acceso segura, flexible y profesional para gestionar tráfico HTTP/HTTPS!</b>
</div>

---

## 📋 Descripción General

HTTP Proxy Server es una solución avanzada para gestionar, auditar y controlar el tráfico HTTP/HTTPS, ideal para empresas y desarrolladores. Puedes ejecutarlo como servicio en Windows o como script Python.

**Características principales:**

- 🔒 Sesiones persistentes y aisladas para cada cliente
- ⚡ API RESTful completa: login, proxy, gestión de sesiones, headers y cookies
- 🛠️ Configuración flexible vía `.env` o variables de entorno
- 📑 Logs detallados de toda la actividad
- 🧩 Documentación interactiva (Swagger UI)

---

## 🚀 ¿Cómo ejecutar el servidor?

### 🖥️ Como ejecutable (Windows)
1. Coloca `HttpProxyServer.exe` en la carpeta deseada y ejecútalo:
  ```bash
  HttpProxyServer.exe
  ```
  El proceso se ejecuta en segundo plano, sin consola visible.

### 🐍 Como script Python (desarrollo)
1. Clona el repositorio y accede a la carpeta:
  ```bash
  git clone <repo_url>
  cd http-proxy-server
  ```
2. Crea un entorno virtual e instala dependencias:
  ```bash
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  ```
3. Ejecuta el servidor:
  ```bash
  python main.py
  ```

---

## ⚙️ Configuración

La configuración es flexible y sigue esta prioridad:
1. Archivo `.env` (en la misma carpeta que el ejecutable/script)
2. Variables de entorno
3. Valores por defecto

**Ejemplo de `.env`:**
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

**Variables de entorno equivalentes:**
```bash
set SERVER_HOST=0.0.0.0
set SERVER_PORT=9000
set LOG_LEVEL=debug
set SESSION_TIMEOUT=1200
set CLEANUP_INTERVAL=600
set ACCESS_LOG=true
```

---

## 🌐 Endpoints principales y casos de uso

> **Recuerda:** Tras crear la sesión, debes enviar el header `X-Session-ID` en todas las peticiones.

### Health Check
`GET /health-check` — Verifica el estado del servidor y la conectividad.

### Crear sesión
`POST /subscribe` — Crea una sesión única para el cliente.
Respuesta:
```json
{
  "status": "OK",
  "session": { "session_id": "..." }
}
```

### Eliminar sesión
`POST /unsubscribe` — Elimina la sesión y borra cookies/cabeceras.

### Configurar headers personalizados
`POST /set-headers` — Define cabeceras HTTP para la sesión.
```json
{
  "Authorization": "Bearer token123",
  "X-Custom-Header": "ValorPersonalizado"
}
```

### Obtener headers actuales
`POST /get-headers` — Devuelve los headers configurados.

### Obtener cookies actuales
`POST /get-cookies` — Devuelve las cookies activas de la sesión.

### Información completa de la sesión
`POST /get-session-info`

### Proxy de peticiones HTTP/HTTPS
`POST /forward` — Reenvía cualquier petición HTTP/HTTPS usando la sesión activa.
```json
{
  "url": "https://api.empresa.com/datos",
  "method": "GET",
  "headers": { "Accept": "application/json", "X-Session-ID": "abc123" }
}
```

### Descarga de archivos
`POST /dowwnload` — Descarga archivos binarios manteniendo la sesión y autenticación.
```json
{
  "url": "https://files.company.com/download/file.zip",
  "method": "GET"
}
```

---

## 📝 Logs

- Todos los eventos se registran en `HttpProxyServer.log`.
- Niveles: debug, info, warning, error.
- Ejemplo:
  ```
  2026-01-15 20:49:00,123 [INFO] __main__ - Aplicación Inicializada correctamente
  2026-01-15 20:49:01,456 [INFO] __main__ - Iniciando verificación de salud del servicio
  ```

---

## 🛑 ¿Cómo detener el servidor?

- **Administrador de tareas**: `Ctrl+Shift+Esc` → buscar `HttpProxyServer.exe` → terminar proceso
- **Línea de comandos**: `taskkill /f /im HttpProxyServer.exe`
- **PowerShell**: `Get-Process -Name "HttpProxyServer" | Stop-Process -Force`

---

## 🌀 Ejemplo de workflow típico

1. Crear sesión: `POST /subscribe`
2. Login en sistema externo usando `/forward`:
   ```bash
   curl -X POST "http://localhost:8000/forward" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://sistema.empresa.com/login",
       "method": "POST",
       "data": {
         "username": "mi_usuario",
         "password": "mi_contraseña"
       },
       "headers": { "Content-Type": "application/x-www-form-urlencoded" }
     }'
   ```
3. Realizar peticiones autenticadas: `POST /forward`
4. Descargar archivos: `POST /dowwnload`
5. Configurar headers personalizados: `POST /set-headers`
6. Logout: `POST /unsubscribe`

---

## 🛠️ Solución de problemas

- **Puerto ocupado**: Cambia el puerto en `.env` o termina el proceso existente.
- **Permisos**: Ejecuta como administrador o usa puertos >1024.
- **Sin internet**: Verifica red, proxy corporativo o firewall.

---

## 🔐 Seguridad

- Soporte HTTPS, validación robusta, logging de auditoría, headers de seguridad, timeouts configurables y más.

---

## 📚 Documentación interactiva

- [Swagger UI](http://localhost:5003/docs)
- [ReDoc](http://localhost:5003/redoc)
- [Health Check](http://localhost:5003/health-check)

---

**Desarrollador:** Raul Mauricio Uñate Castro  
**Versión:** 3.0.0  
**Fecha:** 20 de Enero de 2026