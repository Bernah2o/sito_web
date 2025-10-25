"""
Utilidades JWT para autenticación segura
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, request, jsonify, session
from models import Usuario

class JWTManager:
    """Manejador de tokens JWT para autenticación"""
    
    @staticmethod
    def generate_access_token(user_id, username):
        """
        Genera un token de acceso JWT
        
        Args:
            user_id (int): ID del usuario
            username (str): Nombre de usuario
            
        Returns:
            str: Token JWT codificado
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
    
    @staticmethod
    def generate_refresh_token(user_id, username):
        """
        Genera un token de actualización JWT
        
        Args:
            user_id (int): ID del usuario
            username (str): Nombre de usuario
            
        Returns:
            str: Token JWT de actualización
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
    
    @staticmethod
    def decode_token(token):
        """
        Decodifica y valida un token JWT
        
        Args:
            token (str): Token JWT a decodificar
            
        Returns:
            dict: Payload del token si es válido, None si es inválido
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expirado'}
        except jwt.InvalidTokenError:
            return {'error': 'Token inválido'}
    
    @staticmethod
    def get_token_from_request():
        """
        Extrae el token JWT de la petición HTTP
        
        Returns:
            str: Token JWT o None si no se encuentra
        """
        # Buscar en el header Authorization
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        
        # Buscar en las cookies
        token = request.cookies.get('access_token')
        if token:
            return token
        
        # Buscar en la sesión
        token = session.get('access_token')
        if token:
            return token
        
        return None

def jwt_required(f):
    """
    Decorador para rutas que requieren autenticación JWT
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = JWTManager.get_token_from_request()
        
        if not token:
            return jsonify({'error': 'Token de acceso requerido'}), 401
        
        payload = JWTManager.decode_token(token)
        
        if not payload or 'error' in payload:
            return jsonify({'error': payload.get('error', 'Token inválido')}), 401
        
        if payload.get('type') != 'access':
            return jsonify({'error': 'Tipo de token inválido'}), 401
        
        # Verificar que el usuario existe
        usuario = Usuario.obtener_por_id(payload['user_id'])
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 401
        
        # Agregar información del usuario al contexto
        request.current_user = {
            'id': payload['user_id'],
            'username': payload['username'],
            'usuario': usuario
        }
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """
    Decorador para rutas que requieren autenticación de administrador
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Primero verificar JWT
        token = JWTManager.get_token_from_request()
        
        if not token:
            # Fallback a sesión tradicional para compatibilidad
            if not session.get('usuario_id'):
                return jsonify({'error': 'Acceso no autorizado'}), 401
            
            # Verificar usuario en sesión
            usuario = Usuario.obtener_por_id(session['usuario_id'])
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 401
            
            request.current_user = {
                'id': session['usuario_id'],
                'username': session.get('nombre', ''),
                'usuario': usuario
            }
        else:
            # Validar JWT
            payload = JWTManager.decode_token(token)
            
            if not payload or 'error' in payload:
                return jsonify({'error': payload.get('error', 'Token inválido')}), 401
            
            if payload.get('type') != 'access':
                return jsonify({'error': 'Tipo de token inválido'}), 401
            
            # Verificar que el usuario existe
            usuario = Usuario.obtener_por_id(payload['user_id'])
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 401
            
            request.current_user = {
                'id': payload['user_id'],
                'username': payload['username'],
                'usuario': usuario
            }
        
        return f(*args, **kwargs)
    
    return decorated_function