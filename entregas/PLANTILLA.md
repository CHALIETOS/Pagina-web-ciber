# CiberFaro LAB · Informe de Prácticas y Entrega

**Módulos:** Puesta en Producción Segura (PPS), Hacking Ético y Gestión de Incidentes  
**Ciclo:** Curso de Especialización / Formación Profesional en Ciberseguridad  
**Alumno:** Carlos (CHALIETOS)  
**Fecha:** Noviembre 2026  
**Repositorio del proyecto:** [https://github.com/CHALIETOS/Pagina-web-ciber](https://github.com/CHALIETOS/Pagina-web-ciber)  

---

## Índice
1. [Identificación y Contexto](#identificación-y-contexto)
2. [Sesión 1 · PPS: Despliegue y Observabilidad](#sesión-1--pps-despliegue-y-observabilidad)
3. [Sesión 2 · PPS: Revisión de Configuración y Endurecimiento](#sesión-2--pps-revisión-de-configuración-y-endurecimiento)
4. [Sesión 3 · Hacking Ético: Revisión Autorizada](#sesión-3--hacking-ético-revisión-autorizada)
5. [Sesión 4 · Gestión de Incidentes: Simulación](#sesión-4--gestión-de-incidentes-simulación)
6. [Reto Opcional: Prueba Automatizada de Aislamiento](#reto-opcional-prueba-automatizada-de-aislamiento)
7. [Conclusiones](#conclusiones)

---

## Identificación y Contexto

- **Nombre de la Aplicación:** CiberFaro LAB / CyberLearn
- **Arquitectura:** Cliente-Servidor contenerizado en Docker.
- **Backend:** FastAPI (Python 3.11), Uvicorn, Pydantic, ItsDangerous.
- **Base de Datos:** SQLite 3 persistente montada mediante volumen (`/app/data/ciberfaro.db`).
- **Frontend:** SPA interactiva HTML5, CSS3 cyberpunk (Matrix rain canvas) y Vanilla JS.
- **Alcance de la prueba:** Exclusivamente entorno local de laboratorio en `http://127.0.0.1:8000`.

---

## Sesión 1 · PPS: Despliegue y Observabilidad

### 1.1 Esquema de Arquitectura

```text
       +---------------------------------------------------------+
       |                  Máquina Host (Ubuntu)                  |
       |                                                         |
       |  Navegador Web / curl                                   |
       |  (http://127.0.0.1:8000)                                |
       +----------------------------+----------------------------+
                                    |
                    Mapeo seguro: 127.0.0.1:8000
                                    |
       +----------------------------v----------------------------+
       |               Contenedor Docker (ciberfaro_web)         |
       |                                                         |
       |  +---------------------------------------------------+  |
       |  | Servidor ASGI: Uvicorn (0.0.0.0:8000)             |  |
       |  | Framework: FastAPI (app.main:app)                 |  |
       |  | Usuario: appuser (UID 10001, sin privilegios)     |  |
       |  +-------------------------+-------------------------+  |
       |                            |                            |
       |              Endpoints API | Servidor Estático          |
       |        (/health, /api/...) | (index, dashboard, etc.)   |
       |                            |                            |
       |  +-------------------------v-------------------------+  |
       |  | Capa de Datos: SQLite /app/data/ciberfaro.db       |  |
       |  +-------------------------+-------------------------+  |
       +----------------------------|----------------------------+
                                    |
                     Volumen persistente Docker
                     (Host: ./data -> Contenedor: /app/data)
                                    |
       +----------------------------v----------------------------+
       |           Directorio Local Host (./data/ciberfaro.db)   |
       +---------------------------------------------------------+
```

### 1.2 Explicación Técnica de los Componentes

1. **`Dockerfile`:**
   - Define cómo se construye la imagen inmutable de la aplicación.
   - Utiliza una imagen base mínima `python:3.11-slim` para reducir la superficie de ataque y el tamaño.
   - Implementa el principio de mínimo privilegio creando un usuario dedicado sin privilegios (`appuser`, UID 10001) para que el proceso no corra como `root`.
   - Incorpora la directiva `HEALTHCHECK` nativa para comprobar automáticamente la disponibilidad del servicio.

2. **`compose.yaml`:**
   - Orquesta el despliegue del servicio `web`.
   - Vincula el puerto al loopback local (`127.0.0.1:8000:8000`), evitando exponer el servicio en interfaces de red públicas o LAN.
   - Define el volumen persistente `./data:/app/data` para que la base de datos SQLite no se destruya al reiniciar el contenedor.
   - Carga variables de entorno desde `.env` y establece límites de recursos (CPU y memoria).

3. **El Volumen Persistente (`./data:/app/data`):**
   - Garantiza la persistencia de la información entre destrucciones o recreaciones del contenedor. SQLite almacena sus tablas y registros en `./data/ciberfaro.db`.

4. **El Puerto `127.0.0.1:8000` vs `0.0.0.0:8000`:**
   - Vincular a `127.0.0.1` restringe el tráfico a conexiones originadas únicamente en la misma máquina física.
   - Vincular a `0.0.0.0` expondría el servicio a cualquier equipo de la red local (LAN) o Internet, lo que supondría un riesgo de seguridad en un entorno de desarrollo/laboratorio.

5. **`.env.example`:**
   - Sirve como plantilla documentada de las variables necesarias para el despliegue sin exponer secretos en el repositorio Git.
   - Permite que cada desarrollador o administrador configure su propio `SESSION_SECRET` único.

### 1.3 Comandos Empleados y Salidas Reales

#### Generación de clave segura:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

#### Despliegue con Docker Compose:
```bash
docker compose up --build -d
```
*Salida:*
```text
✔ Network pagina-web-ciber_default Created
✔ Container ciberfaro_web          Started
```

#### Comprobación de estado (`docker compose ps`):
```bash
docker compose ps
```
*Salida:*
```text
NAME            IMAGE                  COMMAND                  SERVICE   CREATED          STATUS                   PORTS
ciberfaro_web   pagina-web-ciber-web   "uvicorn app.main:ap…"   web       28 seconds ago   Up 5 seconds (healthy)   127.0.0.1:8000->8000/tcp
```

#### Comprobación del endpoint de salud (`/health`):
```bash
curl -fsS http://localhost:8000/health
```
*Salida:*
```json
{"status":"ok","service":"CiberFaro LAB","timestamp":"2026-11-17T11:10:59.668006","version":"1.0.0"}
```

#### Consulta de registros (`docker compose logs --tail=30 web`):
```bash
docker compose logs --tail=30 web
```
*Salida relevante:*
```text
ciberfaro_web | 2026-11-17 11:10:54,620 [INFO] [ciberfaro.web] Base de datos SQLite inicializada correctamente en /app/data/ciberfaro.db
ciberfaro_web | INFO:     Application startup complete.
ciberfaro_web | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
ciberfaro_web | INFO:     127.0.0.1:34992 - "GET /health HTTP/1.1" 200 OK
```

### 1.4 Verificación de Persistencia tras Reinicio

1. Se dio de alta el dominio `test-persistencia.es` mediante petición autenticada a la API.
2. Se reinició el contenedor con `docker compose restart web`.
3. Se consultó nuevamente la API `/api/domains`:
```json
{"domains":[{"id":2,"domain_name":"test-persistencia.es","status":"monitorizado","created_at":"..."},{"id":1,"domain_name":"lab-ciberfaro.local","status":"monitorizado","created_at":"..."}]}
```
*Conclusión:* Los datos permanecen íntegros en el volumen del host `./data/ciberfaro.db`.

---

## Sesión 2 · PPS: Revisión de Configuración y Endurecimiento

### 2.1 Cinco Decisiones de Seguridad Identificadas

1. **Ejecución como usuario sin privilegios (`appuser`, UID 10001):**  
   En el `Dockerfile`, la aplicación no se ejecuta como `root`. Si un atacante lograra una ejecución remota de código (RCE) dentro del contenedor, no tendría permisos de superusuario en el sistema de archivos del contenedor ni capacidades administrativas en el host.
2. **Exposición de red restringida a localhost (`127.0.0.1:8000`):**  
   En `compose.yaml`, el binding explícito a la interfaz loopback previene que el puerto quede accesible desde otros equipos de la subred o desde Internet sin autorización expresa.
3. **Gestión externa de secretos (`.env` vs código fuente):**  
   El `SESSION_SECRET` se inyecta por variables de entorno y está explícitamente excluido en `.gitignore`. Nunca se commitean secretos al repositorio.
4. **Almacenamiento seguro de contraseñas (PBKDF2-HMAC-SHA256):**  
   Las contraseñas no se almacenan en texto plano ni con algoritmos obsoletos como MD5 o SHA-1. Se utiliza PBKDF2 con salt criptográfico de 16 bytes y 100,000 iteraciones, mitigando ataques de tablas rainbow y fuerza bruta.
5. **Aislamiento de sesiones y cookies HTTPOnly:**  
   La cookie de sesión `session_token` se emite con el flag `HttpOnly=True` y `SameSite=Lax`, impidiendo que scripts maliciosos de terceros puedan robar la cookie mediante ataques XSS.

### 2.2 Tres Limitaciones del Prototipo Actual

1. **Falta de cifrado en tránsito (HTTP plano):**  
   La aplicación se comunica por HTTP sin TLS nativo en el puerto 8000. Para producción, requiere un reverse proxy (como Nginx o Traefik) con certificados TLS/HTTPS.
2. **Motor SQLite mono-archivo:**  
   SQLite utiliza bloqueos a nivel de archivo para las escrituras. No admite alta concurrencia ni despliegues distribuidos en clúster (requeriría migrar a PostgreSQL/MariaDB).
3. **Ausencia de Rate Limiting por IP:**  
   No existe limitador de peticiones por segundo en el backend, lo que permitiría saturación o ataques reiterados de inicio de sesión si no se añade un middleware o WAF.

### 2.3 Verificación de `.gitignore`

Se verificó mediante `git status` que el archivo `.env` y el directorio `data/` quedan excluidos:
```bash
git status
```
*Salida:*
```text
Archivos sin seguimiento:
	.env.example
	.gitignore
	requirements.txt
```
*(El archivo `.env` no aparece en archivos sin seguimiento ni en el índice Git).*

### 2.4 Checklist de Endurecimiento Priorizado

| Medida de Endurecimiento | Prioridad | Justificación Técnica |
| :--- | :---: | :--- |
| **Añadir Rate Limiting (slowapi / redis)** | **Alta** | Evita ataques de fuerza bruta en `/api/login` y denegación de servicio en endpoints pesados. |
| **Configurar cabeceras HTTP de seguridad (CSP, HSTS, X-Frame-Options)** | **Alta** | Protege al cliente contra ataques de Clickjacking, XSS y downgrade de protocolo. |
| **Establecer sistema de archivos de solo lectura (`read_only: true` en compose)** | **Media** | El contenedor no necesita escribir fuera de `/app/data`, previniendo modificación de binarios en caso de intrusión. |
| **Escaneo automatizado de vulnerabilidades en dependencias (`pip-audit` / `Trivy`)** | **Media** | Detecta CVEs conocidas en librerías de Python o en la imagen base de forma temprana. |
| **Configurar rotación periódica de logs** | **Baja** | Evita que los registros saturen el espacio en disco en despliegues prolongados. |

---

## Sesión 3 · Hacking Ético: Revisión Autorizada

### 3.1 Definición del Alcance (Scope)
- **Objetivo autorizado:** Únicamente la instancia de laboratorio desplegada en `http://127.0.0.1:8000`.
- **Restricciones:** Prohibido atacar activos externos, realizar ataques de fuerza bruta masiva, o pruebas DoS que saturen el host.

### 3.2 Recorrido del Flujo Funcional
1. **Registro:** Creación de cuenta `auditor_test` con correo `auditor@lab.es` en `/api/register`.
2. **Acceso:** Inicio de sesión con credenciales válidas en `/api/login` (recepción de cookie `session_token`).
3. **Panel:** Consulta de información del usuario en `/api/me` y carga del dashboard interactivo.
4. **Alta de dominio:** Registro del dominio `empresa-auditoria.es` en `/api/domains`, verificando la creación de alertas simuladas en `/api/alerts`.
5. **Cierre de sesión:** Llamada a `/api/logout`, borrado de la cookie y revocación del acceso a endpoints protegidos.

### 3.3 Pruebas con Entradas Inválidas y Clasificación de Hallazgos

| ID | Prueba Realizada | Entrada Inyectada | Resultado Observado | Clasificación | Mitigación |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **H-01** | Inyección de Comandos en Alta de Dominio | `dominio.es; cat /etc/passwd` | HTTP 400: *"Formato de dominio inválido"* | **Falso Positivo / Control Efectivo** | La validación por expresión regular estricta bloquea caracteres de shell. |
| **H-02** | Inyección SQL en Formulario de Login | `' OR '1'='1` en campo usuario | HTTP 401: *"Usuario o contraseña incorrectos"* | **Falso Positivo / Control Efectivo** | El uso de consultas parametrizadas con SQLite (`?`) neutraliza la inyección SQL. |
| **H-03** | Inyección XSS en Registro | `<script>alert(1)</script>` como username | HTTP 400: *"Nombre de usuario inválido"* | **Falso Positivo / Control Efectivo** | La restricción a caracteres alfanuméricos (`^[a-zA-Z0-9_\-]+$`) impide etiquetas HTML. |
| **H-04** | Acceso cruzado entre cuentas (IDOR en dominios) | Usuario B intenta `DELETE /api/domains/{id_alice}` | HTTP 404: *"Dominio no encontrado o no pertenece a tu cuenta"* | **Control Efectivo** | El backend filtra explícitamente por `user_id = user['id']`. |
| **H-05** | Ausencia de Rate Limiting en Login | 50 intentos seguidos de contraseña incorrecta | HTTP 401 continuado sin bloqueo temporal | **Indicio de Riesgo** | Implementar bloqueo o retraso exponencial tras 5 fallos consecutivos. |

---

## Sesión 4 · Gestión de Incidentes: Simulación

### 4.1 Escenario del Incidente Simulado
Se detectan múltiples alertas en los registros de auditoría de la aplicación: un atacante ha intentado acceder a la cuenta `admin` y, posteriormente, ha conseguido comprometer una cuenta de prueba `demo` realizando el alta no autorizada de un dominio malicioso `phishing-banco-falso.com`.

### 4.2 Evidencias y Registros Existentes vs Faltantes

- **Evidencias que SÍ ayudan a detectarlo:**
  - Registros en `audit_logs` con `event_type = 'LOGIN_FAILED'` sucesivos provenientes de una misma IP.
  - Registro de `event_type = 'LOGIN_SUCCESS'` seguido inmediatamente de `event_type = 'DOMAIN_ADD'`.
  - Marcas de tiempo ISO en los registros de Docker (`docker compose logs web`).
- **Registros que FALTAN y mejorarían la respuesta:**
  - Falta registrar la cabecera `User-Agent` del cliente para identificar herramientas automatizadas (ej. sqlmap, hydra).
  - Falta geolocalización o reputación de IP.
  - Falta un canal de alerta en tiempo real (ej. webhook o notificación a SIEM) cuando se supera un umbral de fallos.

### 4.3 Cronología del Incidente Simulado

- **10:14:02 UTC:** Comienzan intentos fallidos de autenticación para el usuario `admin` desde la IP `192.168.1.150`.
- **10:14:28 UTC:** El atacante cambia el objetivo al usuario `demo` y acierta la credencial tras 4 intentos.
- **10:15:05 UTC:** Se emite token de sesión para `demo` y se registra `LOGIN_SUCCESS`.
- **10:15:32 UTC:** El atacante registra el dominio `phishing-banco-falso.com` mediante `POST /api/domains`.
- **10:16:10 UTC:** El equipo de seguridad detecta la anomalía mediante la inspección de `docker compose logs web`.

### 4.4 Plan de Respuesta a Incidentes

1. **Fase de Contención:**
   - Invalidación inmediata de todas las sesiones activas cambiando el `SESSION_SECRET` en `.env` y reiniciando el servicio (`docker compose restart web`).
   - Bloqueo de la IP atacante en el firewall del host (`iptables -A INPUT -s 192.168.1.150 -j DROP`).
2. **Fase de Erradicación:**
   - Eliminación del dominio malicioso de la base de datos SQLite.
   - Forzado de cambio de contraseña para el usuario afectado (`demo`).
3. **Fase de Recuperación:**
   - Verificación de la integridad de la base de datos y restauración del servicio.
4. **Lecciones Aprendidas:**
   - Forzar la adopción de contraseñas complejas.
   - Prohibir usuarios por defecto con credenciales conocidas en producción.
   - Integrar alertas automáticas ante más de 5 fallos de autenticación por minuto.

---

## Reto Opcional: Prueba Automatizada de Aislamiento

Para superar el reto opcional, se implementó una suite de pruebas automatizadas con `pytest` en [`tests/test_app.py`](../tests/test_app.py).

### Ejecución de los Tests:
```bash
docker compose exec web pytest -v
```

### Salida Real de la Ejecución:
```text
============================= test session starts ==============================
platform linux -- Python 3.11.18, pytest-9.2.0, pluggy-1.7.0 -- /usr/local/bin/python3.11
cachedir: .pytest_cache
rootdir: /app
plugins: anyio-4.16.0
collected 4 items

tests/test_app.py::test_health_endpoint PASSED                           [ 25%]
tests/test_app.py::test_user_registration_and_login PASSED               [ 50%]
tests/test_app.py::test_domain_validation_rejects_malicious_inputs PASSED [ 75%]
tests/test_app.py::test_reto_opcional_user_isolation PASSED              [100%]

======================== 4 passed in 0.37s =========================
```

### Explicación del Test de Aislamiento (`test_reto_opcional_user_isolation`):
1. El test registra al usuario `Alice` y da de alta su dominio confidencial.
2. Registra al usuario `Bob` (posible atacante).
3. `Bob` consulta `/api/domains` y se comprueba que el dominio de Alice **no aparece**.
4. `Bob` intenta forzar el borrado del dominio de Alice mediante su ID (`DELETE /api/domains/{id_alice}`). El backend rechaza la petición con **HTTP 404** porque el dominio no pertenece al usuario autenticado, demostrando que la aplicación está blindada contra vulnerabilidades IDOR.

---

## Conclusiones

La práctica ha permitido desplegar una aplicación web completa siguiendo los estándares de **Puesta en Producción Segura (PPS)**:
1. Se ha logrado un entorno contenerizado, reproducible y seguro mediante Docker y Docker Compose.
2. Los secretos de sesión se gestionan fuera del código fuente con variables de entorno protegidas.
3. Se verificó la observabilidad mediante el endpoint `/health` y los registros estructurados de eventos de seguridad.
4. La persistencia de datos mediante volúmenes garantiza que los reinicios no suponen pérdida de información.
5. Se validaron los controles defensivos mediante pruebas de penetración manuales y tests automatizados con `pytest`.
