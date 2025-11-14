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
    
    # Configuración de email (compatibilidad SMTP_* y MAIL_*)
    # Variables base (posibles nombres en .env)
    SMTP_HOST = os.environ.get('SMTP_HOST')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    EMAIL_FROM = os.environ.get('EMAIL_FROM')

    # Mapeo para Flask-Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', SMTP_HOST or 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', SMTP_PORT or 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')
    if MAIL_USE_TLS is None:
        # Si no se definió, asumir TLS cuando usamos puerto 587
        MAIL_USE_TLS = MAIL_PORT == 587
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', SMTP_USERNAME)
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', SMTP_PASSWORD)
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', EMAIL_FROM)
    
    # Configuración del sitio web
    WEBSITE_URL = os.environ.get('WEBSITE_URL')
    WEBSITE_NAME = os.environ.get('WEBSITE_NAME')
    
    # Configuración de reCAPTCHA
    RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY')
    RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')

    # Configuración de pagos (Wompi y códigos QR)
    # URL de checkout Wompi (puede configurarse por variable de entorno)
    WOMPI_CHECKOUT_URL = os.environ.get('WOMPI_CHECKOUT_URL')
    # Rutas de archivos de QR dentro de /static (usar solo el filename para url_for)
    NEQUI_QR_FILENAME = os.environ.get('NEQUI_QR_FILENAME', 'img/qr_nequi.jpeg')
    BREB_QR_FILENAME = os.environ.get('BREB_QR_FILENAME', 'img/qr_negocios.jpeg')

    # Enlace directo de pago Nequi (opcional)
    NEQUI_PAYMENT_URL = os.environ.get('NEQUI_PAYMENT_URL')
    # Número de Nequi (celular)
    NEQUI_PHONE_NUMBER = os.environ.get('NEQUI_PHONE_NUMBER')

    # Datos de cuenta Bre-B (opcional)
    BREB_BANK_NAME = os.environ.get('BREB_BANK_NAME')
    BREB_ACCOUNT_TYPE = os.environ.get('BREB_ACCOUNT_TYPE')  # Ej: 'Ahorros' o 'Corriente'
    BREB_ACCOUNT_NUMBER = os.environ.get('BREB_ACCOUNT_NUMBER')
    BREB_ACCOUNT_HOLDER = os.environ.get('BREB_ACCOUNT_HOLDER')

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