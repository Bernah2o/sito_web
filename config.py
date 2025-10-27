import os
from datetime import timedelta
from dotenv import load_dotenv

# Cargar variables de entorno al importar este módulo
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Configuración de base de datos - por defecto MySQL
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'mysql')  # 'mysql' o 'sqlite'
    
    # Configuración MySQL (para producción)
    DB_HOST = os.environ.get('DB_HOST')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_NAME = os.environ.get('DB_NAME')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # Configuración SQLite (para desarrollo)
    SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', 'dh2ocol_dev.db')
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False  # True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    
    # Configuración JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS')))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS')))
    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM')
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo
    UPLOAD_FOLDER = 'static/uploads'
    
    # Configuración de email
    SMTP_HOST = os.environ.get('SMTP_HOST')
    SMTP_PORT = int(os.environ.get('SMTP_PORT'))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    EMAIL_FROM = os.environ.get('EMAIL_FROM')
    
    # Configuración del sitio web
    WEBSITE_URL = os.environ.get('WEBSITE_URL')
    WEBSITE_NAME = os.environ.get('WEBSITE_NAME')

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    DATABASE_TYPE = 'sqlite'  # Usar SQLite en desarrollo
    SQLITE_DB_PATH = 'dh2ocol_dev.db'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    DATABASE_TYPE = 'mysql'  # Usar MySQL en producción

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}