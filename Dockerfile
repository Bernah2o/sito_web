# Usar imagen base oficial de Python
FROM python:3.11-slim

# Establecer variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Copiar script de entrada y darle permisos
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh && \
    dos2unix docker-entrypoint.sh || true

# Crear directorios necesarios
RUN mkdir -p static/uploads logs

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Usar script de entrada personalizado con Gunicorn
CMD ["./docker-entrypoint.sh", "gunicorn", "--config", "gunicorn.conf.py", "app:app"]