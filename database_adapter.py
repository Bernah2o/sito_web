"""
Adaptador de base de datos para DH2OCOL
Maneja conexiones tanto a SQLite (desarrollo) como MySQL (producción)
"""

import sqlite3
import pymysql
import os
from flask import g, current_app
from contextlib import contextmanager


class DatabaseAdapter:
    """Adaptador que maneja múltiples tipos de base de datos"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar el adaptador con la aplicación Flask"""
        app.teardown_appcontext(self.close_db)
        app.get_db = self.get_db
    
    def get_db(self):
        """Obtener conexión a la base de datos según la configuración"""
        if 'db' not in g:
            db_type = current_app.config.get('DATABASE_TYPE', 'mysql')
            if db_type == 'sqlite':
                g.db = self._get_sqlite_connection()
            else:
                g.db = self._get_mysql_connection()
        return g.db
    
    def _get_sqlite_connection(self):
        """Crear conexión SQLite"""
        db_path = current_app.config.get('SQLITE_DB_PATH', 'dh2ocol_dev.db')
        connection = sqlite3.connect(db_path)
        # Configurar row_factory para que devuelva objetos Row (compatibles con dict)
        connection.row_factory = sqlite3.Row
        return SQLiteWrapper(connection)
    
    def _get_mysql_connection(self):
        """Crear conexión MySQL"""
        conn = pymysql.connect(
            host=current_app.config['DB_HOST'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            database=current_app.config['DB_NAME'],
            port=current_app.config['DB_PORT'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return MySQLWrapper(conn)
    
    def close_db(self, error):
        """Cerrar conexión a la base de datos"""
        db = g.pop('db', None)
        if db is not None:
            db.close()


class DatabaseWrapper:
    """Clase base para wrappers de base de datos"""
    
    def __init__(self, connection):
        self.connection = connection
    
    def cursor(self):
        """Obtener cursor de la base de datos"""
        raise NotImplementedError
    
    def commit(self):
        """Confirmar transacción"""
        self.connection.commit()
    
    def rollback(self):
        """Revertir transacción"""
        self.connection.rollback()
    
    def close(self):
        """Cerrar conexión"""
        self.connection.close()


class SQLiteWrapper(DatabaseWrapper):
    """Wrapper para SQLite que emula el comportamiento de MySQL"""
    
    def cursor(self):
        """Obtener cursor SQLite con comportamiento similar a MySQL"""
        return SQLiteCursorWrapper(self.connection.cursor())


class MySQLWrapper(DatabaseWrapper):
    """Wrapper para MySQL"""
    
    def cursor(self):
        """Obtener cursor MySQL"""
        return MySQLCursorWrapper(self.connection.cursor())


class CursorWrapper:
    """Clase base para wrappers de cursor"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def execute(self, query, params=None):
        """Ejecutar consulta"""
        raise NotImplementedError
    
    def fetchone(self):
        """Obtener una fila"""
        raise NotImplementedError
    
    def fetchall(self):
        """Obtener todas las filas"""
        raise NotImplementedError
    
    def close(self):
        """Cerrar cursor"""
        self.cursor.close()


class SQLiteCursorWrapper(CursorWrapper):
    """Wrapper para cursor SQLite que convierte sintaxis MySQL a SQLite"""
    
    def execute(self, query, params=None):
        """Ejecutar consulta convirtiendo sintaxis MySQL a SQLite"""
        # Convertir placeholders de MySQL (%s) a SQLite (?)
        sqlite_query = query.replace('%s', '?')
        
        # Convertir algunas funciones específicas de MySQL
        sqlite_query = sqlite_query.replace('AUTO_INCREMENT', 'AUTOINCREMENT')
        sqlite_query = sqlite_query.replace('BOOLEAN', 'INTEGER')
        sqlite_query = sqlite_query.replace('TRUE', '1')
        sqlite_query = sqlite_query.replace('FALSE', '0')
        
        if params:
            return self.cursor.execute(sqlite_query, params)
        else:
            return self.cursor.execute(sqlite_query)
    
    def fetchone(self):
        """Obtener una fila como diccionario"""
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def fetchall(self):
        """Obtener todas las filas como lista de diccionarios"""
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]


class MySQLCursorWrapper(CursorWrapper):
    """Wrapper para cursor MySQL (sin cambios, mantiene comportamiento original)"""
    
    def execute(self, query, params=None):
        """Ejecutar consulta MySQL"""
        if params:
            return self.cursor.execute(query, params)
        else:
            return self.cursor.execute(query)
    
    def fetchone(self):
        """Obtener una fila"""
        return self.cursor.fetchone()
    
    def fetchall(self):
        """Obtener todas las filas"""
        return self.cursor.fetchall()


# Función de conveniencia para obtener la base de datos
def get_db():
    """Función de conveniencia para obtener la conexión a la base de datos"""
    return current_app.get_db()


@contextmanager
def get_db_transaction():
    """Context manager para transacciones de base de datos"""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise