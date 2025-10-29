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
    
    # API Endpoints para Contador de Visitantes
    @app.route('/api/visitor-count', methods=['POST'])
    def register_visitor():
        """Registrar una nueva visita"""
        from flask import request, jsonify
        try:
            data = request.get_json() or {}
            
            # Obtener información del visitante
            visitor_data = {
                'timestamp': datetime.now(),
                'ip_address': request.remote_addr,
                'user_agent': data.get('userAgent', request.headers.get('User-Agent', '')),
                'referrer': data.get('referrer', ''),
                'page': data.get('page', '/'),
                'session_id': data.get('sessionId', ''),
                'screen_resolution': data.get('screenResolution', ''),
                'language': data.get('language', ''),
                'timezone': data.get('timezone', '')
            }
            
            # Guardar en base de datos
            db = db_adapter.get_db()
            cursor = db.cursor()
            
            # Crear tabla si no existe (compatible con SQLite)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visitor_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    referrer TEXT,
                    page VARCHAR(255),
                    session_id VARCHAR(100),
                    screen_resolution VARCHAR(20),
                    language VARCHAR(10),
                    timezone VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insertar nueva visita
            cursor.execute("""
                INSERT INTO visitor_logs 
                (timestamp, ip_address, user_agent, referrer, page, session_id, 
                 screen_resolution, language, timezone)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                visitor_data['timestamp'],
                visitor_data['ip_address'],
                visitor_data['user_agent'],
                visitor_data['referrer'],
                visitor_data['page'],
                visitor_data['session_id'],
                visitor_data['screen_resolution'],
                visitor_data['language'],
                visitor_data['timezone']
            ))
            
            # Obtener el ID del visitante insertado (compatible con SQLite y MySQL)
            visitor_id = db.connection.lastrowid if hasattr(db.connection, 'lastrowid') else None
            
            # Obtener total de visitantes
            cursor.execute("SELECT COUNT(*) as total FROM visitor_logs")
            result = cursor.fetchone()
            total_visitors = result['total'] if result else 0
            
            db.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'total_visitors': total_visitors,
                'visitor_id': visitor_id,
                'timestamp': visitor_data['timestamp'].isoformat()
            })
            
        except Exception as e:
            import traceback
            print(f"Error registrando visitante: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/visitor-stats')
    def get_visitor_stats():
        """Obtener estadísticas de visitantes"""
        from flask import jsonify
        try:
            db = db_adapter.get_db()
            cursor = db.cursor()
            
            # Total de visitantes
            cursor.execute("SELECT COUNT(*) as total FROM visitor_logs")
            result = cursor.fetchone()
            total_visitors = result['total'] if result else 0
            
            # Visitantes de hoy (compatible con SQLite)
            cursor.execute("""
                SELECT COUNT(*) as today FROM visitor_logs 
                WHERE DATE(timestamp) = DATE('now')
            """)
            result = cursor.fetchone()
            today_visitors = result['today'] if result else 0
            
            # Visitantes únicos (por IP)
            cursor.execute("SELECT COUNT(DISTINCT ip_address) as unique_count FROM visitor_logs")
            result = cursor.fetchone()
            unique_visitors = result['unique_count'] if result else 0
            
            # Visitantes de la última hora (simulando "en línea") - compatible con SQLite
            cursor.execute("""
                SELECT COUNT(DISTINCT session_id) as online FROM visitor_logs 
                WHERE timestamp >= datetime('now', '-1 hour')
            """)
            result = cursor.fetchone()
            online_visitors = result['online'] if result else 0
            
            # Páginas más visitadas
            cursor.execute("""
                SELECT page, COUNT(*) as visits 
                FROM visitor_logs 
                GROUP BY page 
                ORDER BY visits DESC 
                LIMIT 5
            """)
            top_pages = [{'page': row['page'], 'visits': row['visits']} for row in cursor.fetchall()]
            
            cursor.close()
            
            return jsonify({
                'totalVisitors': total_visitors,
                'todayVisitors': today_visitors,
                'uniqueVisitors': unique_visitors,
                'onlineVisitors': online_visitors,
                'topPages': top_pages,
                'lastUpdated': datetime.now().isoformat()
            })
            
        except Exception as e:
            import traceback
            print(f"Error obteniendo estadísticas: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'totalVisitors': 0,
                'todayVisitors': 0,
                'uniqueVisitors': 0,
                'onlineVisitors': 0,
                'topPages': [],
                'error': str(e)
            }), 500
    
    @app.route('/api/analytics', methods=['POST'])
    def register_analytics():
        """Registrar datos de analytics avanzados"""
        from flask import request, jsonify
        try:
            data = request.get_json() or {}
            
            db = db_adapter.get_db()
            cursor = db.cursor()
            
            # Crear tabla de analytics si no existe (compatible con SQLite)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visitor_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    page VARCHAR(255),
                    referrer TEXT,
                    user_agent TEXT,
                    screen_resolution VARCHAR(20),
                    language VARCHAR(10),
                    timezone VARCHAR(50),
                    is_new_visitor BOOLEAN,
                    session_id VARCHAR(100),
                    local_count INTEGER,
                    ip_address VARCHAR(45),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insertar datos de analytics
            cursor.execute("""
                INSERT INTO visitor_analytics 
                (timestamp, page, referrer, user_agent, screen_resolution, 
                 language, timezone, is_new_visitor, session_id, local_count, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.fromtimestamp(data.get('timestamp', 0) / 1000),
                data.get('page', ''),
                data.get('referrer', ''),
                data.get('userAgent', ''),
                data.get('screenResolution', ''),
                data.get('language', ''),
                data.get('timezone', ''),
                data.get('isNewVisitor', False),
                data.get('sessionId', ''),
                data.get('localCount', 0),
                request.remote_addr
            ))
            
            db.commit()
            cursor.close()
            
            return jsonify({
                'success': True,
                'message': 'Analytics registrados correctamente'
            })
            
        except Exception as e:
            print(f"Error registrando analytics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
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