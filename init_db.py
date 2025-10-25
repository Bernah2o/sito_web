#!/usr/bin/env python3
"""
Script para inicializar la base de datos MySQL de DH2OCOL
"""

import os
import pymysql
from config import DevelopmentConfig



def create_mysql_database():
    """Crear la base de datos MySQL si no existe"""
    try:
        # Conectar sin especificar base de datos
        connection = pymysql.connect(
            host=DevelopmentConfig.DB_HOST,
            user=DevelopmentConfig.DB_USER,
            password=DevelopmentConfig.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Crear base de datos
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DevelopmentConfig.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Base de datos MySQL '{DevelopmentConfig.DB_NAME}' creada/verificada")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al crear la base de datos MySQL: {e}")
        return False



def init_mysql_tables():
    """Inicializar tablas en MySQL"""
    try:
        # Conectar a la base de datos
        connection = pymysql.connect(
            host=DevelopmentConfig.DB_HOST,
            user=DevelopmentConfig.DB_USER,
            password=DevelopmentConfig.DB_PASSWORD,
            database=DevelopmentConfig.DB_NAME,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Ejecutar el script SQL desde models.py
            from models import get_mysql_init_sql
            sql_commands = get_mysql_init_sql()
            
            for command in sql_commands:
                if command.strip():
                    cursor.execute(command)
            
            connection.commit()
            print("✅ Tablas MySQL creadas exitosamente")
            print("✅ Datos iniciales insertados")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al inicializar tablas MySQL: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Inicializando base de datos MySQL para DH2OCOL...")
    print("=" * 50)
    
    print("📊 Tipo de base de datos: MySQL")
    
    # Crear base de datos MySQL
    if not create_mysql_database():
        print("\n📋 Verifica que:")
        print("1. MySQL esté ejecutándose")
        print("2. Las credenciales en .env sean correctas")
        print("3. El usuario tenga permisos para crear bases de datos")
        return
    
    if not init_mysql_tables():
        return
    
    print("\n🎉 ¡Base de datos inicializada correctamente!")
    print("\n📋 Credenciales por defecto:")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
    print("\n🌐 Ejecuta 'python app.py' para iniciar la aplicación")

if __name__ == "__main__":
    main()