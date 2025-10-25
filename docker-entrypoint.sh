#!/bin/bash
set -e

echo "🐳 Iniciando contenedor DH2OCOL..."

# Función para esperar a que MySQL esté disponible
wait_for_mysql() {
    echo "⏳ Esperando a que MySQL esté disponible..."
    
    while ! python3 -c "
import pymysql
import os
import sys
try:
    conn = pymysql.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        port=int(os.environ.get('DB_PORT', 3306)),
        connect_timeout=5
    )
    conn.close()
    print('✅ MySQL está disponible')
    sys.exit(0)
except Exception as e:
    print(f'❌ MySQL no disponible: {e}')
    sys.exit(1)
" 2>/dev/null; do
        echo "⏳ MySQL no está listo, esperando 5 segundos..."
        sleep 5
    done
}

# Función para verificar/crear la base de datos
setup_database() {
    echo "🗄️ Configurando base de datos..."
    
    python3 -c "
import pymysql
import os

try:
    # Conectar sin especificar base de datos
    conn = pymysql.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        port=int(os.environ.get('DB_PORT', 3306)),
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    # Crear base de datos si no existe
    db_name = os.environ.get('DB_NAME', 'flaskdb')
    cursor.execute(f'CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    print(f'✅ Base de datos {db_name} verificada/creada')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error configurando base de datos: {e}')
    exit(1)
"
}

# Función para ejecutar migraciones
run_migrations() {
    echo "🔄 Ejecutando migraciones..."
    
    if [ -f "auto_clean_migration.py" ]; then
        echo "📋 Ejecutando migración limpia..."
        python3 auto_clean_migration.py
    else
        echo "⚠️ No se encontró script de migración"
    fi
}

# Función para verificar la configuración
verify_config() {
    echo "🔍 Verificando configuración..."
    
    python3 -c "
import os
from config import config

env = os.environ.get('FLASK_ENV', 'production')
app_config = config[env]

print(f'✅ Entorno: {env}')
print(f'✅ Base de datos: {app_config.DB_HOST}:{app_config.DB_PORT}/{app_config.DB_NAME}')
print(f'✅ Website URL: {app_config.WEBSITE_URL}')
print(f'✅ Debug: {app_config.DEBUG}')
"
}

# Función principal
main() {
    echo "🚀 Iniciando proceso de arranque..."
    
    # Verificar variables de entorno críticas
    if [ -z "$DB_PASSWORD" ]; then
        echo "❌ Error: DB_PASSWORD no está configurada"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        echo "❌ Error: SECRET_KEY no está configurada"
        exit 1
    fi
    
    # Esperar a MySQL
    wait_for_mysql
    
    # Configurar base de datos
    setup_database
    
    # Ejecutar migraciones solo si es el primer arranque
    if [ "$RUN_MIGRATIONS" = "true" ]; then
        run_migrations
    fi
    
    # Verificar configuración
    verify_config
    
    echo "✅ Contenedor listo para recibir tráfico"
    echo "🌐 Aplicación disponible en puerto 5000"
    
    # Ejecutar la aplicación
    exec "$@"
}

# Ejecutar función principal con todos los argumentos
main "$@"