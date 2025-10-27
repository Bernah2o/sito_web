#!/usr/bin/env python3
"""
Aplicación principal de DH2OCOL
Sistema web profesional para gestión de servicios de tanques de agua
"""

import os
import pymysql
from datetime import datetime
from flask import Flask, g
from flask_mail import Mail
from dotenv import load_dotenv
from config import config
from database_adapter import DatabaseAdapter

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask-Mail
mail = Mail()
db_adapter = DatabaseAdapter()

def create_app(config_name='development'):
    """Factory para crear la aplicación Flask"""
    # Asegurar que las variables de entorno estén cargadas
    load_dotenv()
    
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar Flask-Mail
    mail.init_app(app)
    
    # Configurar base de datos
    init_db_connection(app)
    
    # Registrar Blueprints
    from blueprints.main import main_bp
    from blueprints.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Health check endpoint para Docker
    @app.route('/health')
    def health_check():
        """Endpoint de verificación de salud para Docker"""
        try:
            # Health check básico sin dependencia de base de datos
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            }, 200
        except Exception as e:
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }, 500
    
    # Endpoint separado para verificar base de datos
    @app.route('/health/db')
    def health_check_db():
        """Endpoint de verificación de salud de la base de datos"""
        try:
            # Verificar conexión a base de datos usando el adaptador
            db = db_adapter.get_db()
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'database_type': app.config.get('DATABASE_TYPE', 'unknown'),
                'version': '1.0.0'
            }, 200
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }, 503
    
    # Crear directorio de uploads si no existe
    upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_dir, exist_ok=True)
    
    # Agregar filtros personalizados para templates
    @app.template_filter('firebase_url')
    def firebase_url_filter(url):
        """
        Filtro para determinar si una URL es de Firebase y generar la URL correcta
        """
        if not url:
            print("DEBUG: URL vacía recibida en firebase_url_filter")
            return ''
        
        print(f"DEBUG: Procesando URL en firebase_url_filter: {url}")
        
        # Verificar si es una URL completa (HTTP/HTTPS)
        if url.startswith(('http://', 'https://')):
            print(f"DEBUG: URL completa detectada: {url}")
            return url
        
        # Verificar si es una URL de Firebase (más específica)
        firebase_indicators = [
            'firebasestorage.googleapis.com',
            'storage.googleapis.com'
        ]
        
        # Si contiene algún indicador de Firebase, usar la URL directamente
        if any(indicator in url.lower() for indicator in firebase_indicators):
            print(f"DEBUG: URL de Firebase detectada: {url}")
            return url
        
        # Si no es de Firebase, usar url_for para archivos estáticos
        from flask import url_for
        static_url = url_for('static', filename=url)
        print(f"DEBUG: URL estática generada: {static_url}")
        return static_url
    
    return app

def init_db_connection(app):
    """Inicializar conexión a base de datos usando el adaptador multi-entorno"""
    # Inicializar el adaptador de base de datos global
    db_adapter.init_app(app)

# Crear instancia de la aplicación para Gunicorn
# Determinar entorno para producción
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

def main():
    """Función principal para ejecutar la aplicación"""
    # Determinar entorno
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Crear aplicación
    local_app = create_app(env)
    
    # Solo mostrar información detallada en desarrollo
    if env == 'development':
        db_type = local_app.config.get('DATABASE_TYPE', 'mysql').upper()
        print("🚀 Iniciando DH2OCOL...")
        print("=" * 50)
        print(f"🌐 Entorno: {env}")
        print(f"📊 Base de datos: {db_type}")
        print(f"🔧 Debug: {local_app.config['DEBUG']}")
        print("=" * 50)
        print("📋 URLs disponibles:")
        print("   • Sitio web: http://localhost:5000")
        print("   • Panel admin: http://localhost:5000/admin")
        print("   • Credenciales: admin / admin123")
        print("=" * 50)
    else:
        # En producción, solo un mensaje simple
        print(f"🚀 DH2OCOL iniciado en modo {env}")
    
    # Ejecutar aplicación
    local_app.run(
        debug=local_app.config['DEBUG'],
        host='0.0.0.0',
        port=5000
    )

if __name__ == '__main__':
    main()