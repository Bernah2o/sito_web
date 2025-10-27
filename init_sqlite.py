#!/usr/bin/env python3
"""
Script para inicializar la base de datos SQLite para desarrollo
Convierte el esquema MySQL a SQLite y carga datos iniciales
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime


def get_sqlite_schema():
    """Retorna el esquema SQLite convertido desde MySQL"""
    return [
        # Tabla de usuarios
        """CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de servicios
        """CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(200) NOT NULL,
            descripcion TEXT,
            precio DECIMAL(10,2),
            imagen VARCHAR(1000),
            categoria VARCHAR(100),
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de productos
        """CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            precio DECIMAL(10,2),
            categoria VARCHAR(50),
            imagen VARCHAR(1000),
            stock INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de testimonios
        """CREATE TABLE IF NOT EXISTS testimonios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_cliente VARCHAR(100) NOT NULL,
            empresa VARCHAR(100),
            testimonio TEXT NOT NULL,
            calificacion INTEGER DEFAULT 5,
            imagen VARCHAR(1000),
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de contactos
        """CREATE TABLE IF NOT EXISTS contactos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            telefono VARCHAR(20),
            empresa VARCHAR(255),
            servicio_interes VARCHAR(255),
            mensaje TEXT NOT NULL,
            estado VARCHAR(50) DEFAULT 'nuevo',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de medios
        """CREATE TABLE IF NOT EXISTS medios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(255) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            categoria VARCHAR(100) DEFAULT 'general',
            tamano INTEGER,
            descripcion TEXT,
            ruta VARCHAR(1000) NOT NULL,
            fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de configuración
        """CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clave VARCHAR(100) UNIQUE NOT NULL,
            valor TEXT,
            descripcion TEXT,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de quiz_preguntas
        """CREATE TABLE IF NOT EXISTS quiz_preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta TEXT NOT NULL,
            opcion_a VARCHAR(255) NOT NULL,
            opcion_b VARCHAR(255) NOT NULL,
            opcion_c VARCHAR(255) NOT NULL,
            respuesta_correcta CHAR(1) NOT NULL,
            explicacion TEXT,
            orden INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de quiz_resultados
        """CREATE TABLE IF NOT EXISTS quiz_resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            telefono VARCHAR(20),
            puntaje INTEGER NOT NULL,
            total_preguntas INTEGER NOT NULL,
            respuestas_correctas INTEGER NOT NULL,
            tiempo_completado INTEGER,
            fecha_completado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        # Tabla de password_reset_tokens
        """CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(120) NOT NULL,
            token VARCHAR(255) NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_expiracion TIMESTAMP NOT NULL,
            usado INTEGER DEFAULT 0
        )""",
        
        # Tabla de chatbot_conversaciones
        """CREATE TABLE IF NOT EXISTS chatbot_conversaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(255) NOT NULL,
            mensaje_usuario TEXT NOT NULL,
            respuesta_bot TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    ]


def get_initial_data():
    """Retorna los datos iniciales para la base de datos"""
    return {
        'usuarios': [
            ('admin', generate_password_hash('admin123'), 'admin@dh2ocol.com', 'admin', 1),
            ('bdeaguas', generate_password_hash('Mateo2025$'), 'bdeaguas@dh2o.com.co', 'admin', 1)
        ],
        
        'servicios': [
            ('Limpieza y Desinfección de Tanques', 'Servicio completo de limpieza y desinfección de tanques elevados con productos biodegradables', 150000.00, 'limpieza', 1),
            ('Reparación de Tanques', 'Reparación especializada de tanques elevados, sellado de fisuras y cambio de accesorios', 200000.00, 'reparacion', 1),
            ('Instalación de Tanques', 'Instalación profesional de tanques elevados con garantía y certificación', 300000.00, 'instalacion', 1),
            ('Mantenimiento Preventivo', 'Programa de mantenimiento preventivo para tanques elevados', 100000.00, 'mantenimiento', 1)
        ],
        
        'productos': [
            ('Válvula Flotadora', 'Conjunto válvula tanque 1/2 pulg con flotador: controla nivel de agua automático.', 45000, 'Accesorios', 50, 1),
            ('Flanche Adaptador', 'Adaptador PP blanco para salida de tanque de agua.', 25000, 'Accesorios', 30, 1),
            ('Tapa Tanque', 'Tapa para tanque de agua potable, material resistente a UV.', 35000, 'Accesorios', 25, 1),
            ('Filtro de Agua', 'Filtro de sedimentos para entrada de tanque.', 55000, 'Filtros', 20, 1)
        ],
        
        'testimonios': [
            ('María González', 'Residencial Los Pinos', 'Excelente servicio de limpieza de tanques. Muy profesionales y puntuales.', 5, '', 1),
            ('Carlos Rodríguez', 'Empresa ABC', 'El mantenimiento preventivo ha mejorado mucho la calidad del agua.', 5, '', 1),
            ('Ana Martínez', 'Conjunto Residencial', 'Recomiendo totalmente sus servicios. Muy confiables.', 5, '', 1)
        ],
        
        'configuracion': [
            ('empresa_nombre', 'DH2O Colombia', 'Nombre de la empresa'),
            ('empresa_telefono', '+57 300 123 4567', 'Teléfono principal'),
            ('empresa_email', 'info@dh2ocolombia.com', 'Email de contacto'),
            ('empresa_direccion', 'Valledupar, Cesar, Colombia', 'Dirección de la empresa'),
            ('empresa_whatsapp', '+57 300 123 4567', 'WhatsApp de contacto'),
            ('sitio_web_url', 'https://dh2ocolombia.com', 'URL del sitio web')
        ],
        
        'quiz_preguntas': [
            ('¿Cada cuánto tiempo se debe limpiar un tanque de agua?', 'Cada mes', 'Cada 6 meses', 'Cada año', 'B', 'Se recomienda limpiar los tanques cada 6 meses para mantener la calidad del agua.', 1, 1),
            ('¿Qué productos se deben usar para desinfectar un tanque?', 'Cloro doméstico', 'Productos biodegradables especializados', 'Detergente común', 'B', 'Los productos biodegradables especializados son más seguros y efectivos.', 2, 1),
            ('¿Cuál es la capacidad promedio de un tanque elevado residencial?', '500 litros', '1000 litros', '2000 litros', 'B', 'La mayoría de tanques residenciales tienen capacidad de 1000 litros.', 3, 1)
        ]
    }


def create_sqlite_database(db_path='dh2ocol_dev.db'):
    """Crear y configurar la base de datos SQLite"""
    try:
        # Eliminar base de datos existente si existe
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️ Base de datos existente eliminada: {db_path}")
        
        # Crear nueva base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📊 Creando base de datos SQLite: {db_path}")
        
        # Crear tablas
        schema_commands = get_sqlite_schema()
        for command in schema_commands:
            cursor.execute(command)
        
        print("✅ Tablas creadas exitosamente")
        
        # Insertar datos iniciales
        initial_data = get_initial_data()
        
        # Insertar usuarios
        cursor.executemany(
            "INSERT INTO usuarios (username, password_hash, email, role, activo) VALUES (?, ?, ?, ?, ?)",
            initial_data['usuarios']
        )
        
        # Insertar servicios
        cursor.executemany(
            "INSERT INTO servicios (nombre, descripcion, precio, categoria, activo) VALUES (?, ?, ?, ?, ?)",
            initial_data['servicios']
        )
        
        # Insertar productos
        cursor.executemany(
            "INSERT INTO productos (nombre, descripcion, precio, categoria, stock, activo) VALUES (?, ?, ?, ?, ?, ?)",
            initial_data['productos']
        )
        
        # Insertar testimonios
        cursor.executemany(
            "INSERT INTO testimonios (nombre_cliente, empresa, testimonio, calificacion, imagen, activo) VALUES (?, ?, ?, ?, ?, ?)",
            initial_data['testimonios']
        )
        
        # Insertar configuración
        cursor.executemany(
            "INSERT INTO configuracion (clave, valor, descripcion) VALUES (?, ?, ?)",
            initial_data['configuracion']
        )
        
        # Insertar preguntas del quiz
        cursor.executemany(
            "INSERT INTO quiz_preguntas (pregunta, opcion_a, opcion_b, opcion_c, respuesta_correcta, explicacion, orden, activo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            initial_data['quiz_preguntas']
        )
        
        conn.commit()
        conn.close()
        
        print("✅ Datos iniciales insertados exitosamente")
        print(f"🎉 Base de datos SQLite creada: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear la base de datos SQLite: {e}")
        return False


def main():
    """Función principal"""
    print("🚀 Inicializando base de datos SQLite para desarrollo...")
    print("=" * 60)
    
    db_path = os.environ.get('SQLITE_DB_PATH', 'dh2ocol_dev.db')
    
    if create_sqlite_database(db_path):
        print("\n🎉 ¡Base de datos SQLite inicializada correctamente!")
        print("\n📋 Credenciales por defecto:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("   Usuario: bdeaguas")
        print("   Contraseña: Mateo2025$")
        print(f"\n📁 Archivo de base de datos: {db_path}")
        print("\n🌐 Configura DATABASE_TYPE=sqlite en tu .env y ejecuta 'python app.py'")
    else:
        print("\n❌ Error al inicializar la base de datos")


if __name__ == "__main__":
    main()