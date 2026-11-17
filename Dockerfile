# ==============================================================================
# Dockerfile - CiberFaro LAB (Puesta en Producción Segura)
# ==============================================================================

# 1. Imagen base oficial mínima (reduce superficie de ataque y vulnerabilidades CVE)
FROM python:3.11-slim

# 2. Variables de entorno de Python seguras
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# 3. Instalación de dependencias de Python en capa cacheable
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Creación de usuario no privilegiado (Principio de Mínimo Privilegio - Sesión 2)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/false -M appuser

# 5. Copia del código fuente de la aplicación
COPY . .

# 6. Creación y asignación de permisos para el directorio del volumen persistente
RUN mkdir -p /app/data && \
    chown -R appuser:appgroup /app/data /app

# 7. Cambiar al usuario sin privilegios
USER appuser

# 8. Puerto expuesto dentro del contenedor
EXPOSE 8000

# 9. Healthcheck nativo de contenedor (Observabilidad - Sesión 1)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 10. Comando de ejecución de producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
