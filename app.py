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

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask-Mail
mail = Mail()

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
            # Verificar conexión a base de datos usando la función del app
            db = app.get_db()
            cursor = db.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
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
    
    return app

def init_db_connection(app):
    """Inicializar conexión a base de datos"""
    
    def get_db():
        """Obtener conexión a la base de datos"""
        if 'db' not in g:
            g.db = pymysql.connect(
                host=app.config['DB_HOST'],
                user=app.config['DB_USER'],
                password=app.config['DB_PASSWORD'],
                database=app.config['DB_NAME'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        return g.db
    
    def close_db(error):
        """Cerrar conexión a la base de datos"""
        db = g.pop('db', None)
        if db is not None:
            db.close()
    
    # Registrar funciones en el contexto de la aplicación
    app.teardown_appcontext(close_db)
    
    # Hacer get_db disponible globalmente
    app.get_db = get_db

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
        print("🚀 Iniciando DH2OCOL...")
        print("=" * 50)
        print(f"🌐 Entorno: {env}")
        print(f"📊 Base de datos: MySQL")
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