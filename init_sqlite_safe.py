#!/usr/bin/env python3
"""
Script seguro para inicializar la base de datos SQLite de DH2OCOL
Este script NO contiene datos sensibles y es seguro para el repositorio.
"""

import sqlite3
import hashlib
import getpass
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_tables(cursor):
    """Crear todas las tablas necesarias"""
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            activo INTEGER DEFAULT 1,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de servicios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(200) NOT NULL,
            descripcion TEXT,
            precio DECIMAL(10,2),
            imagen VARCHAR(255),
            categoria VARCHAR(100),
            activo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de testimonios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS testimonios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_cliente VARCHAR(100) NOT NULL,
            empresa VARCHAR(100),
            testimonio TEXT NOT NULL,
            calificacion INTEGER DEFAULT 5,
            imagen VARCHAR(1000),
            activo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de contactos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contactos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            telefono VARCHAR(20),
            empresa VARCHAR(255),
            servicio_interes VARCHAR(255),
            mensaje TEXT NOT NULL,
            estado VARCHAR(50) DEFAULT 'nuevo',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de tokens de reset de contraseña
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(120) NOT NULL,
            token VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE
        )
    ''')

def insert_default_services(cursor):
    """Insertar servicios por defecto (datos no sensibles)"""
    services = [
        ('Limpieza y Desinfección de Tanques', 'Servicio completo de limpieza y desinfección de tanques elevados con productos biodegradables', 150000.00, 'limpieza'),
        ('Mantenimiento Preventivo', 'Mantenimiento preventivo de sistemas de almacenamiento de agua', 120000.00, 'mantenimiento'),
        ('Instalación de Accesorios', 'Instalación de accesorios para tanques elevados', 80000.00, 'instalacion'),
        ('Consultoría en Calidad del Agua', 'Asesoría especializada en calidad y tratamiento del agua', 200000.00, 'consultoria')
    ]
    
    for service in services:
        cursor.execute('''
            INSERT OR IGNORE INTO servicios (nombre, descripcion, precio, categoria)
            VALUES (?, ?, ?, ?)
        ''', service)

def create_admin_user(cursor):
    """Crear usuario administrador de forma interactiva"""
    print("\n🔐 Configuración del usuario administrador")
    print("=" * 50)
    
    # Solicitar datos del administrador
    username = input("Nombre de usuario admin: ").strip()
    if not username:
        username = "admin"
        print(f"Usando nombre por defecto: {username}")
    
    email = input("Email del administrador: ").strip()
    if not email:
        email = "admin@dh2o.com.co"
        print(f"Usando email por defecto: {email}")
    
    # Solicitar contraseña de forma segura
    while True:
        password = getpass.getpass("Contraseña del administrador: ")
        if len(password) < 6:
            print("❌ La contraseña debe tener al menos 6 caracteres")
            continue
        
        confirm_password = getpass.getpass("Confirmar contraseña: ")
        if password != confirm_password:
            print("❌ Las contraseñas no coinciden")
            continue
        break
    
    # Hash de la contraseña con Werkzeug (compatible con producción)
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO usuarios (username, password_hash, email, role)
            VALUES (?, ?, ?, 'admin')
        ''', (username, password_hash, email))
        
        print(f"✅ Usuario administrador '{username}' creado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear usuario administrador: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Inicializando base de datos SQLite para DH2OCOL...")
    print("=" * 50)
    
    db_path = 'dh2ocol_dev.db'
    
    try:
        # Conectar a SQLite
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        print("📊 Creando tablas...")
        create_tables(cursor)
        
        print("📋 Insertando servicios por defecto...")
        insert_default_services(cursor)
        
        print("👤 Configurando usuario administrador...")
        if not create_admin_user(cursor):
            return
        
        # Confirmar cambios
        connection.commit()
        connection.close()
        
        print("\n🎉 ¡Base de datos SQLite inicializada correctamente!")
        print(f"📁 Archivo de base de datos: {db_path}")
        print("\n🌐 Ejecuta 'python app.py' para iniciar la aplicación")
        
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")

if __name__ == "__main__":
    main()