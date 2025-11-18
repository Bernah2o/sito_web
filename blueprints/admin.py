from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import uuid
import io
import csv
from datetime import datetime
from PIL import Image, ImageOps
from jwt_utils import JWTManager, admin_required
from firebase_storage import upload_file, delete_file, is_firebase_available
from database_adapter import get_db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Configuración para subida de imágenes
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
# Extensiones y límite para videos/imágenes en servicios
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi'}
MAX_MEDIA_SIZE = 25 * 1024 * 1024  # 25MB para videos

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file, categoria):
    """Guardar imagen de producto en Firebase Storage y retornar la URL pública"""
    if not file:
        print("Error: No se proporcionó archivo")
        return None
        
    if not file.filename:
        print("Error: Archivo sin nombre")
        return None
    
    print(f"Procesando archivo: {file.filename}")
    print(f"Tipo de contenido: {file.content_type}")
    
    if not allowed_file(file.filename):
        print(f"Error: Formato de archivo no permitido: {file.filename}")
        print(f"Extensiones permitidas: {ALLOWED_EXTENSIONS}")
        return None
    
    if not is_firebase_available():
        print("Firebase Storage no está disponible")
        return None
    
    try:
        # Verificar que el archivo tenga contenido
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size == 0:
            print("Error: El archivo está vacío")
            return None
        
        print(f"Tamaño del archivo: {file_size} bytes")
        
        # Validar que es realmente una imagen válida
        try:
            file_content = file.read()
            file.seek(0)  # Reset file pointer
            
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(file_content))
            img.verify()  # Verificar que es una imagen válida
            print(f"Validación de imagen exitosa - Formato: {img.format}, Tamaño: {img.size}")
            
            # Reset file pointer again after validation
            file.seek(0)
            
        except Exception as img_error:
            print(f"Error: Formato de imagen no válido - {img_error}")
            return None
        
        # Subir archivo a Firebase Storage con optimización específica por categoría
        firebase_url = upload_file(file, folder="productos", optimize_image=True, product_category=categoria)
        
        if firebase_url:
            print(f"Imagen subida exitosamente a Firebase: {firebase_url}")
            return firebase_url
        else:
            print("Error al subir imagen a Firebase Storage")
            return None
            
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        import traceback
        traceback.print_exc()
        return None

def login_required(f):
    """Decorador para requerir login en rutas de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
def index():
    """Ruta base de admin - redirige al dashboard o login"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('admin.login'))

@admin_bp.route('/medios')
@login_required
def medios():
    """Gestión de archivos multimedia"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM medios ORDER BY fecha_subida DESC')
        files_data = cursor.fetchall()
        
        # Convertir a lista de diccionarios para facilitar el uso en template
        files = []
        for file_data in files_data:
            file_dict = {
                    'id': file_data['id'],
                    'name': file_data['nombre'],
                    'filename': file_data['filename'],
                    'type': file_data['tipo'],
                    'category': file_data.get('categoria', 'general'),
                    'size': file_data['tamano'],
                    'description': file_data['descripcion'],
                    'path': file_data['ruta'],
                    'upload_date': file_data['fecha_subida']
                }
            files.append(file_dict)
        
        return render_template('admin/medios.html', files=files)
        
    except Exception as e:
        print(f"Error al cargar medios: {e}")
        flash('Error al cargar archivos multimedia', 'error')
        return render_template('admin/medios.html', files=[])

@admin_bp.route('/medios/upload', methods=['POST'])
@login_required
def upload_media_file():
    """Subir archivo multimedia a Firebase Storage"""
    try:
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('admin.medios'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('admin.medios'))
        
        if not is_firebase_available():
            flash('Firebase Storage no está disponible', 'error')
            return redirect(url_for('admin.medios'))
        
        # Obtener categoría del formulario
        category = request.form.get('category', 'general')
        
        # Mapear categorías a carpetas
        category_folders = {
            'carousel': 'carousel',
            'general': 'general'
        }
        
        # Determinar carpeta de destino
        folder_name = category_folders.get(category, 'general')
        
        # Determinar tipo de archivo
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            file_type = 'image'
        elif file_ext in ['mp4', 'avi', 'mov', 'wmv']:
            file_type = 'video'
        elif file_ext == 'pdf':
            file_type = 'pdf'
        else:
            file_type = 'other'
        
        # Subir archivo a Firebase Storage
        firebase_url = upload_file(file, folder=folder_name, optimize_image=(file_type == 'image'))
        
        if not firebase_url:
            flash('Error al subir archivo a Firebase Storage', 'error')
            return redirect(url_for('admin.medios'))
        
        # Obtener datos del formulario
        file_name = request.form.get('file_name') or file.filename
        description = request.form.get('description', '')
        
        # Estimar tamaño del archivo (Firebase no proporciona esto directamente)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        # Guardar en base de datos con la URL de Firebase
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
                INSERT INTO medios (nombre, filename, tipo, categoria, tamano, descripcion, ruta)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (file_name, file.filename, file_type, category, file_size, description, firebase_url))
        
        db.commit()
        flash('Archivo subido exitosamente a Firebase Storage', 'success')
        
    except Exception as e:
        print(f"Error al subir archivo: {e}")
        flash('Error al subir archivo', 'error')
    
    return redirect(url_for('admin.medios'))

@admin_bp.route('/medios/delete/<int:file_id>', methods=['DELETE'])
@login_required
def delete_media_file(file_id):
    """Eliminar archivo multimedia de Firebase Storage"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener información del archivo
        cursor.execute("SELECT filename, ruta FROM medios WHERE id = %s", (file_id,))
        
        file_data = cursor.fetchone()
        if not file_data:
            return jsonify({'success': False, 'message': 'Archivo no encontrado'})
        
        filename = file_data['filename']
        firebase_url = file_data['ruta']
        
        # Eliminar archivo de Firebase Storage
        if firebase_url:
            if is_firebase_available():
                success = delete_file(firebase_url)
                if not success:
                    return jsonify({'success': False, 'message': 'Error al eliminar archivo de Firebase Storage'})
            else:
                return jsonify({'success': False, 'message': 'Firebase Storage no está disponible'})
        
        # Eliminar de base de datos
        cursor.execute("DELETE FROM medios WHERE id = %s", (file_id,))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Archivo eliminado exitosamente de Firebase Storage'})
        
    except Exception as e:
        print(f"Error al eliminar archivo: {e}")
        return jsonify({'success': False, 'message': 'Error al eliminar archivo'})

@admin_bp.route('/medios/delete-multiple', methods=['DELETE'])
@login_required
def delete_multiple_media_files():
    """Eliminar múltiples archivos multimedia de Firebase Storage"""
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])
        
        if not file_ids:
            return jsonify({'success': False, 'message': 'No se seleccionaron archivos'})
        
        if not is_firebase_available():
            return jsonify({'success': False, 'message': 'Firebase Storage no está disponible'})
        
        db = get_db()
        cursor = db.cursor()
        
        deleted_count = 0
        failed_count = 0
        
        for file_id in file_ids:
            # Obtener información del archivo
            cursor.execute("SELECT filename, ruta FROM medios WHERE id = %s", (file_id,))
            
            file_data = cursor.fetchone()
            if file_data:
                filename = file_data['filename']
                firebase_url = file_data['ruta']
                
                # Eliminar archivo de Firebase Storage
                firebase_success = True
                if firebase_url:
                    firebase_success = delete_file(firebase_url)
                
                if firebase_success:
                    # Eliminar de base de datos solo si se eliminó de Firebase exitosamente
                    cursor.execute("DELETE FROM medios WHERE id = %s", (file_id,))
                    deleted_count += 1
                else:
                    failed_count += 1
        
        db.commit()
        
        if failed_count > 0:
            return jsonify({'success': False, 'message': f'{deleted_count} archivos eliminados, {failed_count} fallaron'})
        else:
            return jsonify({'success': True, 'message': f'{deleted_count} archivos eliminados exitosamente de Firebase Storage'})
        
    except Exception as e:
        print(f"Error al eliminar archivos: {e}")
        return jsonify({'success': False, 'message': 'Error al eliminar archivos'})

@admin_bp.route('/medios/filter/<category>')
@login_required
def filter_medios_by_category(category):
    """Filtrar archivos multimedia por categoría"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        if category == 'all':
            cursor.execute('SELECT * FROM medios ORDER BY fecha_subida DESC')
        else:
            cursor.execute('SELECT * FROM medios WHERE categoria = %s ORDER BY fecha_subida DESC', (category,))
        
        files_data = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        files = []
        for file_data in files_data:
            file_dict = {
                    'id': file_data['id'],
                    'name': file_data['nombre'],
                    'filename': file_data['filename'],
                    'type': file_data['tipo'],
                    'category': file_data.get('categoria', 'general'),
                    'size': file_data['tamano'],
                    'description': file_data['descripcion'],
                    'path': file_data['ruta'],
                    'upload_date': file_data['fecha_subida']
                }
            files.append(file_dict)
        
        return jsonify({'success': True, 'files': files})
        
    except Exception as e:
        print(f"Error al filtrar medios: {e}")
        return jsonify({'success': False, 'message': 'Error al filtrar archivos'})

@admin_bp.route('/medios/update-category/<int:file_id>', methods=['POST'])
@login_required
def update_file_category(file_id):
    """Actualizar categoría de un archivo multimedia"""
    try:
        data = request.get_json()
        new_category = data.get('category', 'general')
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("UPDATE medios SET categoria = %s WHERE id = %s", (new_category, file_id))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Categoría actualizada exitosamente'})
        
    except Exception as e:
        print(f"Error al actualizar categoría: {e}")
        return jsonify({'success': False, 'message': 'Error al actualizar categoría'})

@admin_bp.route('/visitor-logs')
@login_required
def visitor_logs():
    """Página de administración para ver registros de visitantes"""
    try:
        # Filtros desde query params
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page')
        q = request.args.get('q')
        limit = int(request.args.get('limit', 100))

        db = get_db()
        cursor = db.cursor()

        # Determinar tipo de base de datos
        db_type = current_app.config.get('DATABASE_TYPE', 'mysql').lower()

        # Estadísticas
        cursor.execute("SELECT COUNT(*) as total FROM visitor_logs")
        total_row = cursor.fetchone()
        total_visitors = total_row['total'] if total_row else 0

        if db_type == 'sqlite':
            cursor.execute("""
                SELECT COUNT(*) as today FROM visitor_logs
                WHERE DATE(timestamp) = DATE('now')
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) as today FROM visitor_logs
                WHERE DATE(timestamp) = CURDATE()
            """)
        today_row = cursor.fetchone()
        today_visitors = today_row['today'] if today_row else 0

        cursor.execute("SELECT COUNT(DISTINCT ip_address) as unique_count FROM visitor_logs")
        unique_row = cursor.fetchone()
        unique_visitors = unique_row['unique_count'] if unique_row else 0

        if db_type == 'sqlite':
            cursor.execute("""
                SELECT COUNT(DISTINCT session_id) as online FROM visitor_logs
                WHERE timestamp >= datetime('now', '-1 hour')
            """)
        else:
            cursor.execute("""
                SELECT COUNT(DISTINCT session_id) as online FROM visitor_logs
                WHERE timestamp >= (NOW() - INTERVAL 1 HOUR)
            """)
        online_row = cursor.fetchone()
        online_visitors = online_row['online'] if online_row else 0

        # Construir consulta base para logs
        query = "SELECT id, timestamp, page, ip_address, referrer, user_agent, session_id, language, screen_resolution, timezone FROM visitor_logs"
        conditions = []
        params = []

        if start_date:
            conditions.append("timestamp >= %s")
            params.append(f"{start_date} 00:00:00")
        if end_date:
            conditions.append("timestamp <= %s")
            params.append(f"{end_date} 23:59:59")
        if page:
            conditions.append("page LIKE %s")
            params.append(f"%{page}%")
        if q:
            conditions.append("(ip_address LIKE %s OR session_id LIKE %s OR user_agent LIKE %s)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        logs = cursor.fetchall()

        # Top páginas
        cursor.execute("""
            SELECT page, COUNT(*) as visits
            FROM visitor_logs
            GROUP BY page
            ORDER BY visits DESC
            LIMIT 10
        """)
        top_pages = cursor.fetchall()

        # Países a partir de language (ej: es-CO -> CO) o timezone
        country_counts = {}
        name_map = {
            'CO': 'Colombia', 'US': 'Estados Unidos', 'MX': 'México',
            'ES': 'España', 'GB': 'Reino Unido', 'AR': 'Argentina', 'CL': 'Chile',
            'PE': 'Perú', 'EC': 'Ecuador', 'VE': 'Venezuela', 'BR': 'Brasil'
        }
        tz_map = {
            'america/bogota': 'CO',
            'america/new_york': 'US',
            'america/mexico_city': 'MX',
            'europe/madrid': 'ES',
            'europe/london': 'GB',
        }
        for row in logs:
            lang = row.get('language') or ''
            country_code = None
            if '-' in lang:
                parts = lang.split('-')
                if len(parts) >= 2:
                    country_code = parts[1].upper()
            if not country_code:
                tz = (row.get('timezone') or '').lower()
                country_code = tz_map.get(tz)
            country_name = name_map.get(country_code, country_code or 'Desconocido')
            country_counts[country_name] = country_counts.get(country_name, 0) + 1

        top_countries = sorted(
            [{'country': k, 'visits': v} for k, v in country_counts.items()],
            key=lambda x: x['visits'],
            reverse=True
        )[:10]

        cursor.close()

        stats = {
            'total': total_visitors,
            'today': today_visitors,
            'unique': unique_visitors,
            'online': online_visitors
        }

        filters = {
            'start_date': start_date or '',
            'end_date': end_date or '',
            'page': page or '',
            'q': q or '',
            'limit': limit
        }

        return render_template('admin/visitor_logs.html', logs=logs, stats=stats, top_pages=top_pages, filters=filters, top_countries=top_countries)

    except Exception as e:
        print(f"Error cargando visitor logs: {e}")
        flash('Error al cargar registros de visitantes', 'error')
        return render_template('admin/visitor_logs.html', logs=[], stats={'total':0,'today':0,'unique':0,'online':0}, top_pages=[], filters={}, top_countries=[])

@admin_bp.route('/medios/categories')
@login_required
def get_categories():
    """Obtener todas las categorías disponibles para medios"""
    try:
        # Solo devolver las categorías permitidas para medios
        allowed_categories = ['general', 'carousel']
        
        return jsonify({'success': True, 'categories': allowed_categories})
        
    except Exception as e:
        print(f"Error al obtener categorías: {e}")
        return jsonify({'success': False, 'message': 'Error al obtener categorías'})
    else:
        return redirect(url_for('admin.login'))

def get_db():
    """Obtener conexión a la base de datos"""
    return current_app.get_db()

@admin_bp.route('/visitor-logs/export')
@login_required
def visitor_logs_export():
    """Exportar registros de visitantes a CSV según filtros"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page')
        q = request.args.get('q')

        db = get_db()
        cursor = db.cursor()

        query = "SELECT id, timestamp, page, ip_address, referrer, user_agent, session_id, language, screen_resolution, timezone FROM visitor_logs"
        conditions = []
        params = []

        if start_date:
            conditions.append("timestamp >= %s")
            params.append(f"{start_date} 00:00:00")
        if end_date:
            conditions.append("timestamp <= %s")
            params.append(f"{end_date} 23:59:59")
        if page:
            conditions.append("page LIKE %s")
            params.append(f"%{page}%")
        if q:
            conditions.append("(ip_address LIKE %s OR session_id LIKE %s OR user_agent LIKE %s)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"]) 

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id','timestamp','page','ip_address','referrer','user_agent','session_id','language','screen_resolution','timezone'])
        for r in rows:
            writer.writerow([
                r.get('id'), r.get('timestamp'), r.get('page'), r.get('ip_address'),
                r.get('referrer'), r.get('user_agent'), r.get('session_id'), r.get('language'),
                r.get('screen_resolution'), r.get('timezone')
            ])

        resp = make_response(output.getvalue())
        resp.headers['Content-Type'] = 'text/csv; charset=utf-8'
        resp.headers['Content-Disposition'] = 'attachment; filename="visitor_logs.csv"'
        return resp
    except Exception as e:
        current_app.logger.exception('Error exportando CSV de visitantes: %s', e)
        return jsonify({'success': False, 'message': 'Error al exportar CSV'}), 500


@admin_bp.route('/visitor-logs/cleanup', methods=['POST'])
@login_required
def visitor_logs_cleanup():
    """Eliminar registros anteriores a N días"""
    try:
        db = get_db()
        cursor = db.cursor()
        db_type = current_app.config.get('DATABASE_TYPE', 'mysql').lower()

        payload = request.get_json(silent=True) or {}
        days = int(payload.get('days', 90))
        if days <= 0 or days > 3650:
            return jsonify({'success': False, 'message': 'Valor de días inválido'}), 400

        if db_type == 'sqlite':
            delete_query = "DELETE FROM visitor_logs WHERE timestamp < datetime('now', ? || ' day')"
            cursor.execute(delete_query, (f'-{days}',))
        else:
            delete_query = "DELETE FROM visitor_logs WHERE timestamp < (NOW() - INTERVAL %s DAY)"
            cursor.execute(delete_query, (days,))

        db.commit()
        cursor.close()
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.exception('Error limpiando registros antiguos: %s', e)
        return jsonify({'success': False, 'message': 'Error interno al limpiar'}), 500

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login de administrador con JWT"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('SELECT id, username, password_hash FROM usuarios WHERE username = %s AND activo = TRUE', (username,))
            
            user = cursor.fetchone()
            
            if user:
                user_id = user['id'] if isinstance(user, dict) else user[0]
                user_username = user['username'] if isinstance(user, dict) else user[1]
                password_hash = user['password_hash'] if isinstance(user, dict) else user[2]
                
                if check_password_hash(password_hash, password):
                    # Generar tokens JWT
                    access_token = JWTManager.generate_access_token(user_id, user_username)
                    refresh_token = JWTManager.generate_refresh_token(user_id, user_username)
                    
                    # Mantener sesión tradicional para compatibilidad
                    session['admin_logged_in'] = True
                    session['admin_user_id'] = user_id
                    session['admin_username'] = user_username
                    session['access_token'] = access_token
                    session['refresh_token'] = refresh_token
                    
                    # Crear respuesta con cookies seguras
                    response = make_response(redirect(url_for('admin.dashboard')))
                    
                    # Configurar cookies JWT
                    response.set_cookie(
                        'access_token',
                        access_token,
                        max_age=int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()),
                        httponly=True,
                        secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
                        samesite='Lax'
                    )
                    
                    response.set_cookie(
                        'refresh_token',
                        refresh_token,
                        max_age=int(current_app.config['JWT_REFRESH_TOKEN_EXPIRES'].total_seconds()),
                        httponly=True,
                        secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
                        samesite='Lax'
                    )
                    
                    flash('Bienvenido al panel de administración', 'success')
                    return response
            
            flash('Credenciales incorrectas', 'error')
            
        except Exception as e:
            print(f"Error en login: {e}")
            flash('Error al iniciar sesión', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    """Logout de administrador con limpieza de JWT"""
    # Limpiar sesión
    session.clear()
    
    # Crear respuesta de redirección
    response = make_response(redirect(url_for('admin.login')))
    
    # Limpiar cookies JWT
    response.set_cookie('access_token', '', expires=0, httponly=True)
    response.set_cookie('refresh_token', '', expires=0, httponly=True)
    
    flash('Sesión cerrada correctamente', 'info')
    return response

@admin_bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    """Renovar token de acceso usando refresh token"""
    refresh_token = request.cookies.get('refresh_token') or session.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token no encontrado'}), 401
    
    payload = JWTManager.decode_token(refresh_token)
    
    if not payload or 'error' in payload:
        return jsonify({'error': payload.get('error', 'Refresh token inválido')}), 401
    
    if payload.get('type') != 'refresh':
        return jsonify({'error': 'Tipo de token inválido'}), 401
    
    # Generar nuevo access token
    new_access_token = JWTManager.generate_access_token(payload['user_id'], payload['username'])
    
    # Actualizar sesión
    session['access_token'] = new_access_token
    
    # Crear respuesta con nueva cookie
    response = make_response(jsonify({'message': 'Token renovado exitosamente'}))
    response.set_cookie(
        'access_token',
        new_access_token,
        max_age=int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()),
        httponly=True,
        secure=current_app.config.get('SESSION_COOKIE_SECURE', False),
        samesite='Lax'
    )
    
    return response

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Panel principal de administración"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Estadísticas básicas
        cursor.execute('SELECT COUNT(*) as total FROM servicios WHERE activo = TRUE')
        total_servicios = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM productos WHERE activo = TRUE')
        total_productos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM contactos WHERE estado = 'nuevo'")
        contactos_nuevos = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM testimonios WHERE activo = TRUE')
        total_testimonios = cursor.fetchone()['total']
        
        cursor.execute('SELECT * FROM contactos ORDER BY id DESC LIMIT 5')
        contactos_recientes = cursor.fetchall()
        
        stats = {
            'servicios': total_servicios,
            'productos': total_productos,
            'contactos_nuevos': contactos_nuevos,
            'testimonios': total_testimonios
        }
        
        return render_template('admin/dashboard.html', stats=stats, contactos_recientes=contactos_recientes, fecha_actual=datetime.now())
        
    except Exception as e:
        print(f"Error en dashboard: {e}")
        return render_template('admin/dashboard.html', stats={}, contactos_recientes=[], fecha_actual=datetime.now())

@admin_bp.route('/servicios')
@login_required
def servicios():
    """Gestión de servicios"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM servicios ORDER BY nombre')
        servicios_data = cursor.fetchall()
        
        return render_template('admin/servicios.html', servicios=servicios_data)
        
    except Exception as e:
        print(f"Error al cargar servicios: {e}")
        return render_template('admin/servicios.html', servicios=[])

@admin_bp.route('/servicios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_servicio():
    """Crear nuevo servicio"""
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            precio_base = float(request.form.get('precio_base', 0))
            media_url = None

            db = get_db()
            cursor = db.cursor()
            
            # Manejar media (imagen o video) opcional
            if 'media' in request.files:
                file = request.files['media']
                if file and file.filename:
                    # Validar tamaño
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    if file_size > MAX_MEDIA_SIZE:
                        flash('El archivo es demasiado grande. Máximo 25MB para videos.', 'error')
                        return render_template('admin/nuevo_servicio.html')
                    
                    # Subir a Firebase (optimiza si es imagen)
                    media_url = upload_file(file, folder='servicios', optimize_image=True)
                    if not media_url:
                        flash('No se pudo subir el archivo a Firebase.', 'error')
                        return render_template('admin/nuevo_servicio.html')
            
            cursor.execute("""
                    INSERT INTO servicios (nombre, descripcion, precio_base, imagen, activo)
                    VALUES (%s, %s, %s, %s, TRUE)
                """, (nombre, descripcion, precio_base, media_url))
            
            db.commit()
            flash('Servicio creado exitosamente', 'success')
            return redirect(url_for('admin.servicios'))
            
        except Exception as e:
            print(f"Error al crear servicio: {e}")
            flash('Error al crear servicio', 'error')
    
    return render_template('admin/nuevo_servicio.html')

@admin_bp.route('/productos')
@login_required
def productos():
    """Gestión de productos"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM productos ORDER BY categoria, nombre')
        productos_data = cursor.fetchall()
        
        return render_template('admin/productos.html', productos=productos_data)
        
    except Exception as e:
        print(f"Error al cargar productos: {e}")
        return render_template('admin/productos.html', productos=[])

@admin_bp.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    """Crear nuevo producto"""
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            precio = float(request.form.get('precio', 0))
            categoria = request.form.get('categoria')
            
            # Manejar la imagen
            imagen_filename = None
            if 'imagen' in request.files:
                file = request.files['imagen']
                if file.filename != '':
                    # Verificar tamaño del archivo
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    
                    if file_size > MAX_FILE_SIZE:
                        flash('El archivo es demasiado grande. Máximo 5MB permitido.', 'error')
                        return render_template('admin/nuevo_producto.html')
                    
                    imagen_filename = save_product_image(file, categoria)
                    if not imagen_filename:
                        flash('Formato de imagen no válido. Use JPG, PNG o GIF.', 'error')
                        return render_template('admin/nuevo_producto.html')
            
            db = get_db()
            cursor = db.cursor()
            
            # Insertar producto con o sin imagen
            cursor.execute("""
                    INSERT INTO productos (nombre, descripcion, precio, categoria, imagen, activo)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                """, (nombre, descripcion, precio, categoria, imagen_filename))
            
            db.commit()
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('admin.productos'))
            
        except Exception as e:
            print(f"Error al crear producto: {e}")
            flash('Error al crear producto', 'error')
    
    return render_template('admin/nuevo_producto.html')

@admin_bp.route('/contactos')
@login_required
def contactos():
    """Gestión de contactos"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM contactos ORDER BY id DESC')
        contactos_data = cursor.fetchall()
        
        return render_template('admin/contactos.html', contactos=contactos_data)
        
    except Exception as e:
        print(f"Error al cargar contactos: {e}")
        return render_template('admin/contactos.html', contactos=[])

@admin_bp.route('/contactos/<int:contacto_id>/marcar-leido', methods=['POST'])
@login_required
def marcar_contacto_leido(contacto_id):
    """Marcar contacto como leído"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("UPDATE contactos SET estado = 'leido' WHERE id = %s", (contacto_id,))
        
        db.commit()
        flash('Contacto marcado como leído', 'success')
        
    except Exception as e:
        print(f"Error al marcar contacto: {e}")
        flash('Error al actualizar contacto', 'error')
    
    return redirect(url_for('admin.contactos'))

@admin_bp.route('/contactos/eliminar/<int:contacto_id>', methods=['POST'])
@login_required
def eliminar_contacto(contacto_id):
    """Eliminar un mensaje de contacto"""
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("DELETE FROM contactos WHERE id = %s", (contacto_id,))
        db.commit()

        flash('Mensaje de contacto eliminado exitosamente', 'success')
    except Exception as e:
        print(f"Error al eliminar contacto: {e}")
        flash('Error al eliminar el mensaje de contacto', 'error')

    return redirect(url_for('admin.contactos'))

@admin_bp.route('/testimonios')
@login_required
def testimonios():
    """Gestión de testimonios"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM testimonios ORDER BY id DESC')
        testimonios_data = cursor.fetchall()
        
        return render_template('admin/testimonios.html', testimonios=testimonios_data)
        
    except Exception as e:
        print(f"Error al cargar testimonios: {e}")
        return render_template('admin/testimonios.html', testimonios=[])

@admin_bp.route('/testimonios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_testimonio():
    """Crear nuevo testimonio"""
    if request.method == 'POST':
        try:
            nombre_cliente = request.form.get('nombre_cliente')
            empresa = request.form.get('empresa')
            testimonio = request.form.get('testimonio')
            calificacion = int(request.form.get('calificacion', 5))
            
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                    INSERT INTO testimonios (nombre_cliente, empresa, testimonio, calificacion, activo)
                    VALUES (%s, %s, %s, %s, TRUE)
                """, (nombre_cliente, empresa, testimonio, calificacion))
            
            db.commit()
            flash('Testimonio creado exitosamente', 'success')
            return redirect(url_for('admin.testimonios'))
            
        except Exception as e:
            print(f"Error al crear testimonio: {e}")
            flash('Error al crear testimonio', 'error')
    
    # Si es GET, redirigir a la página de testimonios donde está el modal
    return redirect(url_for('admin.testimonios'))



@admin_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    """Configuración del sitio"""
    if request.method == 'POST':
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Obtener datos del formulario
            config_data = {
                'nombre_empresa': request.form.get('nombre_empresa', ''),
                'telefono': request.form.get('telefono', ''),
                'email': request.form.get('email', ''),
                'whatsapp': request.form.get('whatsapp', ''),
                'direccion': request.form.get('direccion', ''),
                'descripcion': request.form.get('descripcion', ''),
                'horarios': request.form.get('horarios', ''),
                'app_url': request.form.get('app_url', ''),
                'facebook': request.form.get('facebook', ''),
                'instagram': request.form.get('instagram', ''),
                'youtube': request.form.get('youtube', ''),
                'linkedin': request.form.get('linkedin', ''),
                'meta_description': request.form.get('meta_description', ''),
                'palabras_clave': request.form.get('palabras_clave', '')
            }
            
            # Actualizar cada configuración
            for clave, valor in config_data.items():
                cursor.execute("""
                        INSERT INTO configuracion (clave, valor) VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE valor = VALUES(valor)
                    """, (clave, valor))
            
            db.commit()
            flash('Configuración actualizada exitosamente', 'success')
            
        except Exception as e:
            print(f"Error al actualizar configuración: {e}")
            flash('Error al actualizar configuración', 'error')
    
    # Cargar configuración actual
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT clave, valor FROM configuracion')
        config_rows = cursor.fetchall()
        
        # Convertir a diccionario
        config = {}
        for row in config_rows:
            config[row['clave']] = row['valor']
        
        # Obtener estadísticas
        cursor.execute('SELECT COUNT(*) as total FROM servicios')
        servicios_count = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM productos')
        productos_count = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM contactos')
        contactos_count = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM testimonios')
        testimonios_count = cursor.fetchone()['total']
        
        stats = {
            'servicios': servicios_count,
            'productos': productos_count,
            'contactos': contactos_count,
            'testimonios': testimonios_count
        }
        
        return render_template('admin/configuracion.html', config=config, stats=stats)
        
    except Exception as e:
        print(f"Error al cargar configuración: {e}")
        return render_template('admin/configuracion.html', config={}, stats={})

@admin_bp.route('/servicios/editar/<int:servicio_id>', methods=['GET', 'POST'])
@login_required
def editar_servicio(servicio_id):
    """Editar servicio existente"""
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            precio_base = float(request.form.get('precio_base', 0))
            media_url = None
            previous_media_url = None
            
            db = get_db()
            cursor = db.cursor()
            # Obtener URL anterior del medio para borrarlo si se reemplaza
            try:
                cursor.execute("SELECT imagen FROM servicios WHERE id = %s", (servicio_id,))
                row = cursor.fetchone()
                if row:
                    # Soporta row como dict o tupla
                    if isinstance(row, dict):
                        previous_media_url = row.get('imagen')
                    else:
                        try:
                            previous_media_url = row[4] if len(row) > 4 else None
                        except Exception:
                            previous_media_url = None
            except Exception as qerr:
                print(f"No se pudo obtener medio anterior del servicio {servicio_id}: {qerr}")
            
            # Manejar media (imagen o video) opcional
            if 'media' in request.files:
                file = request.files['media']
                if file and file.filename:
                    # Validar tamaño
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    if file_size > MAX_MEDIA_SIZE:
                        flash('El archivo es demasiado grande. Máximo 25MB para videos.', 'error')
                        return redirect(url_for('admin.servicios'))
                    
                    # Subir a Firebase (optimiza si es imagen)
                    media_url = upload_file(file, folder='servicios', optimize_image=True)
                    if not media_url:
                        flash('No se pudo subir el archivo a Firebase.', 'error')
                        return redirect(url_for('admin.servicios'))
                    # Si se subió nuevo medio, eliminar el anterior para ahorrar espacio
                    if previous_media_url and is_firebase_available():
                        try:
                            if previous_media_url != media_url:
                                deleted = delete_file(previous_media_url)
                                if not deleted:
                                    print(f"Advertencia: No se pudo eliminar el medio anterior en Firebase del servicio {servicio_id}")
                        except Exception as derr:
                            print(f"Error al eliminar medio anterior del servicio {servicio_id}: {derr}")
            
            if media_url:
                cursor.execute("""
                        UPDATE servicios SET nombre = %s, descripcion = %s, precio_base = %s, imagen = %s
                        WHERE id = %s
                    """, (nombre, descripcion, precio_base, media_url, servicio_id))
            else:
                cursor.execute("""
                        UPDATE servicios SET nombre = %s, descripcion = %s, precio_base = %s
                        WHERE id = %s
                    """, (nombre, descripcion, precio_base, servicio_id))
            
            db.commit()
            flash('Servicio actualizado exitosamente', 'success')
            return redirect(url_for('admin.servicios'))
            
        except Exception as e:
            print(f"Error al actualizar servicio: {e}")
            flash('Error al actualizar servicio', 'error')
    
    return redirect(url_for('admin.servicios'))

@admin_bp.route('/servicios/eliminar/<int:servicio_id>', methods=['POST'])
@login_required
def eliminar_servicio(servicio_id):
    """Eliminar servicio"""
    try:
        db = get_db()
        cursor = db.cursor()

        # Obtener URL del medio para eliminarlo de Firebase
        imagen_url = None
        try:
            cursor.execute("SELECT imagen FROM servicios WHERE id = %s", (servicio_id,))
            row = cursor.fetchone()
            if row:
                if isinstance(row, dict):
                    imagen_url = row.get('imagen')
                else:
                    try:
                        imagen_url = row[4] if len(row) > 4 else None
                    except Exception:
                        imagen_url = None
        except Exception as qerr:
            print(f"No se pudo obtener imagen del servicio {servicio_id} antes de eliminar: {qerr}")

        # Intentar eliminar archivo en Firebase si existe
        if imagen_url and is_firebase_available():
            try:
                firebase_deleted = delete_file(imagen_url)
                if not firebase_deleted:
                    print(f"Advertencia: No se pudo eliminar el archivo en Firebase para servicio {servicio_id}")
            except Exception as derr:
                print(f"Error al eliminar archivo de Firebase para servicio {servicio_id}: {derr}")
        
        # Eliminar registro de BD
        cursor.execute("DELETE FROM servicios WHERE id = %s", (servicio_id,))
        db.commit()
        flash('Servicio eliminado exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al eliminar servicio: {e}")
        flash('Error al eliminar servicio', 'error')
    
    return redirect(url_for('admin.servicios'))

@admin_bp.route('/servicios/toggle/<int:servicio_id>', methods=['POST'])
@login_required
def toggle_servicio(servicio_id):
    """Cambiar estado activo/inactivo de servicio"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("UPDATE servicios SET activo = NOT activo WHERE id = %s", (servicio_id,))
        
        db.commit()
        flash('Estado del servicio actualizado exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al cambiar estado del servicio: {e}")
        flash('Error al cambiar estado del servicio', 'error')
    
    return redirect(url_for('admin.servicios'))

@admin_bp.route('/productos/editar/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    """Editar producto existente"""
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            categoria = request.form.get('categoria')
            descripcion = request.form.get('descripcion')
            precio = float(request.form.get('precio', 0))

            # Obtener URL de imagen anterior para eliminarla si se reemplaza
            imagen_anterior_url = None
            try:
                db_prev = get_db()
                cur_prev = db_prev.cursor()
                cur_prev.execute("SELECT imagen FROM productos WHERE id = %s", (producto_id,))
                producto_prev = cur_prev.fetchone()
                if producto_prev:
                    imagen_anterior_url = producto_prev['imagen'] if isinstance(producto_prev, dict) else (
                        producto_prev[4] if len(producto_prev) > 4 else None
                    )
            except Exception as e_prev:
                print(f"No se pudo obtener imagen anterior del producto {producto_id}: {e_prev}")

            # Manejar la imagen
            imagen_filename = None
            if 'imagen' in request.files:
                file = request.files['imagen']
                if file.filename != '':
                    # Verificar tamaño del archivo
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)

                    if file_size > MAX_FILE_SIZE:
                        flash('El archivo es demasiado grande. Máximo 5MB permitido.', 'error')
                        return redirect(url_for('admin.productos'))

                    imagen_filename = save_product_image(file, categoria)
                    if not imagen_filename:
                        flash('Formato de imagen no válido. Use JPG, PNG o GIF.', 'error')
                        return redirect(url_for('admin.productos'))
                    # Si se subió nueva imagen, eliminar la anterior en Firebase para ahorrar espacio
                    if imagen_anterior_url and is_firebase_available():
                        try:
                            if imagen_anterior_url != imagen_filename:
                                success_del = delete_file(imagen_anterior_url)
                                if not success_del:
                                    print(f"Advertencia: No se pudo eliminar la imagen anterior en Firebase del producto {producto_id}")
                        except Exception as del_err:
                            print(f"Error al eliminar imagen anterior del producto {producto_id}: {del_err}")

            db = get_db()
            cursor = db.cursor()

            # Actualizar producto con o sin imagen
            if imagen_filename:
                cursor.execute("""
                        UPDATE productos SET nombre = %s, categoria = %s, descripcion = %s, precio = %s, imagen = %s
                        WHERE id = %s
                    """, (nombre, categoria, descripcion, precio, imagen_filename, producto_id))
            else:
                cursor.execute("""
                        UPDATE productos SET nombre = %s, categoria = %s, descripcion = %s, precio = %s
                        WHERE id = %s
                    """, (nombre, categoria, descripcion, precio, producto_id))

            db.commit()
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('admin.productos'))

        except Exception as e:
            print(f"Error al actualizar producto: {e}")
            flash('Error al actualizar producto', 'error')
    
    return redirect(url_for('admin.productos'))

@admin_bp.route('/productos/eliminar/<int:producto_id>', methods=['POST'])
@login_required
def eliminar_producto(producto_id):
    """Eliminar producto y su imagen de Firebase Storage"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener información del producto antes de eliminarlo
        cursor.execute("SELECT nombre, imagen FROM productos WHERE id = %s", (producto_id,))
        producto_data = cursor.fetchone()
        
        if not producto_data:
            flash('Producto no encontrado', 'error')
            return redirect(url_for('admin.productos'))
        
        producto_nombre = producto_data['nombre']
        imagen_url = producto_data['imagen']
        
        # Eliminar imagen de Firebase Storage si existe
        firebase_success = True
        if imagen_url and is_firebase_available():
            firebase_success = delete_file(imagen_url)
            if not firebase_success:
                print(f"Advertencia: No se pudo eliminar la imagen de Firebase para el producto {producto_nombre}")
        
        # Eliminar producto de la base de datos
        cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
        db.commit()
        
        if firebase_success:
            flash('Producto e imagen eliminados exitosamente', 'success')
        else:
            flash('Producto eliminado, pero hubo un problema al eliminar la imagen', 'warning')
        
    except Exception as e:
        print(f"Error al eliminar producto: {e}")
        flash('Error al eliminar producto', 'error')
    
    return redirect(url_for('admin.productos'))

@admin_bp.route('/testimonios/editar/<int:testimonio_id>', methods=['POST'])
@login_required
def editar_testimonio(testimonio_id):
    """Editar testimonio existente"""
    try:
        nombre_cliente = request.form.get('nombre_cliente')
        empresa = request.form.get('empresa')
        testimonio = request.form.get('testimonio')
        calificacion = int(request.form.get('calificacion', 5))
        activo = True if request.form.get('activo') else 0
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
                UPDATE testimonios 
                SET nombre_cliente = %s, empresa = %s, testimonio = %s, calificacion = %s, activo = %s
                WHERE id = %s
            """, (nombre_cliente, empresa, testimonio, calificacion, activo, testimonio_id))
        
        db.commit()
        flash('Testimonio actualizado exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al actualizar testimonio: {e}")
        flash('Error al actualizar testimonio', 'error')
    
    return redirect(url_for('admin.testimonios'))

@admin_bp.route('/testimonios/toggle/<int:testimonio_id>', methods=['POST'])
@login_required
def toggle_testimonio(testimonio_id):
    """Activar/desactivar testimonio"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener estado actual
        cursor.execute("SELECT activo FROM testimonios WHERE id = %s", (testimonio_id,))
        
        result = cursor.fetchone()
        if result:
            nuevo_estado = 0 if result['activo'] else 1
            
            cursor.execute("UPDATE testimonios SET activo = %s WHERE id = %s", (nuevo_estado, testimonio_id))
            
            db.commit()
            flash(f'Testimonio {"activado" if nuevo_estado else "desactivado"} exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al cambiar estado del testimonio: {e}")
        flash('Error al cambiar estado del testimonio', 'error')
    
    return redirect(url_for('admin.testimonios'))

@admin_bp.route('/testimonios/eliminar/<int:testimonio_id>', methods=['POST'])
@login_required
def eliminar_testimonio(testimonio_id):
    """Eliminar testimonio"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM testimonios WHERE id = %s", (testimonio_id,))
        
        db.commit()
        flash('Testimonio eliminado exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al eliminar testimonio: {e}")
        flash('Error al eliminar testimonio', 'error')
    
    return redirect(url_for('admin.testimonios'))

@admin_bp.route('/backup')
@login_required
def backup_db():
    """Crear backup de la base de datos"""
    try:
        import shutil
        import datetime
        
        flash('Backup de MySQL no implementado aún', 'warning')
        
    except Exception as e:
        print(f"Error al crear backup: {e}")
        flash('Error al crear backup', 'error')
    
    return redirect(url_for('admin.configuracion'))

# =====================
# Contenido Institucional (Nosotros)
# =====================

def ensure_nosotros_tables(cursor):
    """Crear tabla de secciones institucionales si no existe"""
    try:
        from flask import current_app
        db_type = current_app.config.get('DATABASE_TYPE', 'mysql').lower()

        if db_type == 'sqlite':
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS institucional_secciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave VARCHAR(50) UNIQUE NOT NULL,
                    titulo VARCHAR(255) NOT NULL,
                    contenido TEXT,
                    orden INTEGER DEFAULT 0,
                    activo INTEGER DEFAULT 1,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Asegurar columna de imagen (SQLite)
            try:
                cursor.execute("PRAGMA table_info(institucional_secciones)")
                cols = cursor.fetchall()
                col_names = [c['name'] if isinstance(c, dict) else c[1] for c in cols]
                if 'imagen' not in col_names:
                    cursor.execute("ALTER TABLE institucional_secciones ADD COLUMN imagen TEXT")
            except Exception as col_err:
                print(f"Advertencia al agregar columna imagen (sqlite): {col_err}")
        else:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS institucional_secciones (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    clave VARCHAR(50) UNIQUE NOT NULL,
                    titulo VARCHAR(255) NOT NULL,
                    contenido TEXT,
                    orden INT DEFAULT 0,
                    activo BOOLEAN DEFAULT TRUE,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """
            )
            # Asegurar columna de imagen (MySQL)
            try:
                cursor.execute("SHOW COLUMNS FROM institucional_secciones LIKE 'imagen'")
                exists = cursor.fetchone()
                if not exists:
                    cursor.execute("ALTER TABLE institucional_secciones ADD COLUMN imagen TEXT NULL")
            except Exception as col_err:
                print(f"Advertencia al agregar columna imagen (mysql): {col_err}")
    except Exception as e:
        print(f"Error creando tabla institucional_secciones: {e}")

def seed_nosotros_sections(cursor):
    """Insertar secciones por defecto si no existen"""
    try:
        secciones = [
            ("quienes_somos", "Quiénes Somos", "Somos DH2OCOL, un equipo comprometido con brindar servicios de limpieza y desinfección de tanques elevados con estándares profesionales, seguridad y enfoque al cliente.", 0, 1),
            ("mision", "Misión", "Nuestra misión es garantizar agua segura mediante la limpieza y desinfección profesional de tanques elevados.", 1, 1),
            ("vision", "Visión", "Ser la empresa líder en la región en servicios de mantenimiento de tanques, reconocida por calidad, cumplimiento y resultados.", 2, 1),
            ("historia", "Nuestra Historia", "Nacimos con el propósito de mejorar la salud y bienestar de hogares y empresas, acumulando experiencia y confianza en la comunidad.", 3, 1),
            ("compromiso_ambiental", "Compromiso Ambiental", "Operamos con procesos responsables, uso eficiente de recursos y productos certificados, minimizando el impacto ambiental.", 4, 1),
            ("valores", "Nuestros Valores", "Confianza, cumplimiento, responsabilidad, transparencia y servicio al cliente.", 5, 1),
            ("seguridad_calidad", "Seguridad y Calidad", "Protocolos de bioseguridad, supervisión técnica y estándares de calidad en cada intervención.", 6, 1),
            ("cobertura_regional", "Cobertura Regional", "Atendemos Valledupar, el Cesar y municipios aledaños.", 7, 1),
            ("certificaciones", "Certificaciones y Cumplimientos", "Cumplimos normativas sanitarias y buenas prácticas en manejo de agua potable.", 8, 1),
        ]
        for clave, titulo, contenido, orden, activo in secciones:
            cursor.execute("SELECT id FROM institucional_secciones WHERE clave=%s", (clave,))
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    """
                    INSERT INTO institucional_secciones (clave, titulo, contenido, orden, activo)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (clave, titulo, contenido, orden, activo)
                )
    except Exception as e:
        print(f"Error insertando secciones por defecto: {e}")

@admin_bp.route('/nosotros', methods=['GET', 'POST'])
@login_required
def admin_nosotros():
    """Gestión de contenidos institucionales (Nosotros)"""
    db = get_db()
    cursor = db.cursor()
    ensure_nosotros_tables(cursor)

    if request.method == 'POST':
        try:
            # Procesar formulario: sections[clave][campo]
            sections = request.form.getlist('section_keys')
            for clave in sections:
                titulo = request.form.get(f'sections[{clave}][titulo]', '').strip()
                contenido = request.form.get(f'sections[{clave}][contenido]', '').strip()
                orden = int(request.form.get(f'sections[{clave}][orden]', '0') or 0)
                activo = True if request.form.get(f'sections[{clave}][activo]') else 0

                # Manejo de imagen opcional por sección
                imagen_url = None
                file = request.files.get(f'sections[{clave}][imagen]')
                if file and file.filename:
                    # Validar tamaño
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    if file_size > MAX_FILE_SIZE:
                        flash(f'El archivo para {titulo} es demasiado grande. Máximo 5MB.', 'error')
                        return redirect(url_for('admin.admin_nosotros'))

                    # Validar extensión
                    if not allowed_file(file.filename):
                        flash(f'Formato de imagen no permitido en {titulo}. Usa JPG, PNG o GIF.', 'error')
                        return redirect(url_for('admin.admin_nosotros'))

                    # Subir a Firebase
                    imagen_url = upload_file(file, folder='nosotros', optimize_image=True)
                    if not imagen_url:
                        flash(f'No se pudo subir la imagen de {titulo} a Firebase.', 'error')
                        return redirect(url_for('admin.admin_nosotros'))

                cursor.execute("SELECT id FROM institucional_secciones WHERE clave=%s", (clave,))
                row = cursor.fetchone()
                if row:
                    # Eliminar imagen anterior si se subió nueva
                    if imagen_url:
                        try:
                            cursor.execute("SELECT imagen FROM institucional_secciones WHERE clave=%s", (clave,))
                            prev = cursor.fetchone()
                            prev_url = None
                            if prev:
                                if isinstance(prev, dict):
                                    prev_url = prev.get('imagen')
                                else:
                                    try:
                                        prev_url = prev[0]
                                    except Exception:
                                        prev_url = None
                            if prev_url and prev_url != imagen_url and is_firebase_available():
                                delete_file(prev_url)
                        except Exception as del_err:
                            print(f"Advertencia al eliminar imagen anterior ({clave}): {del_err}")

                    # Actualizar con o sin imagen
                    if imagen_url:
                        cursor.execute(
                            """
                            UPDATE institucional_secciones
                            SET titulo=%s, contenido=%s, orden=%s, activo=%s, imagen=%s
                            WHERE clave=%s
                            """,
                            (titulo, contenido, orden, activo, imagen_url, clave)
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE institucional_secciones
                            SET titulo=%s, contenido=%s, orden=%s, activo=%s
                            WHERE clave=%s
                            """,
                            (titulo, contenido, orden, activo, clave)
                        )
                else:
                    cursor.execute(
                        """
                        INSERT INTO institucional_secciones (clave, titulo, contenido, orden, activo)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (clave, titulo, contenido, orden, activo)
                    )
                    # Si hay imagen, actualizar inmediatamente el campo
                    if imagen_url:
                        try:
                            cursor.execute(
                                "UPDATE institucional_secciones SET imagen=%s WHERE clave=%s",
                                (imagen_url, clave)
                            )
                        except Exception as ins_img_err:
                            print(f"Error guardando imagen inicial para {clave}: {ins_img_err}")

            db.commit()
            flash('Contenido institucional actualizado exitosamente', 'success')
            return redirect(url_for('admin.admin_nosotros'))
        except Exception as e:
            db.rollback()
            print(f"Error actualizando contenido institucional: {e}")
            flash('Error al actualizar el contenido', 'error')

    # GET: cargar secciones
    seed_nosotros_sections(cursor)
    cursor.execute("SELECT * FROM institucional_secciones ORDER BY orden, id")
    secciones = cursor.fetchall()
    return render_template('admin/nosotros.html', secciones=secciones)

@admin_bp.route('/nosotros/quienes-somos', methods=['GET', 'POST'])
@login_required
def nosotros_quienes_somos():
    """Gestión dedicada de las secciones 'Quiénes Somos' y 'Nuestros Valores'"""
    db = get_db()
    cursor = db.cursor()
    ensure_nosotros_tables(cursor)

    if request.method == 'POST':
        try:
            clave = (request.form.get('clave') or 'quienes_somos').strip()
            titulo = request.form.get('titulo', '').strip()
            contenido = request.form.get('contenido', '').strip()
            orden = int(request.form.get('orden', '0') or 0)
            activo = True if request.form.get('activo') else 0

            # Manejo de imagen opcional
            imagen_url = None
            file = request.files.get('imagen')
            if file and file.filename:
                # Validar tamaño
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                if file_size > MAX_FILE_SIZE:
                    flash('La imagen es demasiado grande. Máximo 5MB.', 'error')
                    return redirect(url_for('admin.nosotros_quienes_somos'))

                # Validar extensión
                if not allowed_file(file.filename):
                    flash('Formato de imagen no permitido. Usa JPG, PNG o GIF.', 'error')
                    return redirect(url_for('admin.nosotros_quienes_somos'))

                imagen_url = upload_file(file, folder='nosotros', optimize_image=True)
                if not imagen_url:
                    flash('No se pudo subir la imagen a Firebase.', 'error')
                    return redirect(url_for('admin.nosotros_quienes_somos'))

            # Buscar sección por clave
            cursor.execute("SELECT id, imagen FROM institucional_secciones WHERE clave=%s", (clave,))
            row = cursor.fetchone()
            if row:
                # Eliminar imagen anterior si se sube una nueva
                if imagen_url:
                    try:
                        prev_url = None
                        if isinstance(row, dict):
                            prev_url = row.get('imagen')
                        else:
                            try:
                                prev_url = row[1]
                            except Exception:
                                prev_url = None
                        if prev_url and prev_url != imagen_url and is_firebase_available():
                            delete_file(prev_url)
                    except Exception as del_err:
                        print(f"Advertencia al eliminar imagen anterior ({clave}): {del_err}")

                # Actualizar sección
                if imagen_url:
                    cursor.execute(
                        """
                        UPDATE institucional_secciones
                        SET titulo=%s, contenido=%s, orden=%s, activo=%s, imagen=%s
                        WHERE clave=%s
                        """,
                        (titulo or ('Quiénes Somos' if clave=='quienes_somos' else 'Nuestros Valores'), contenido, orden, activo, imagen_url, clave)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE institucional_secciones
                        SET titulo=%s, contenido=%s, orden=%s, activo=%s
                        WHERE clave=%s
                        """,
                        (titulo or ('Quiénes Somos' if clave=='quienes_somos' else 'Nuestros Valores'), contenido, orden, activo, clave)
                    )
            else:
                # Insertar nueva sección si no existe
                cursor.execute(
                    """
                    INSERT INTO institucional_secciones (clave, titulo, contenido, orden, activo)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (clave, titulo or ('Quiénes Somos' if clave=='quienes_somos' else 'Nuestros Valores'), contenido, orden, activo)
                )
                if imagen_url:
                    try:
                        cursor.execute(
                            "UPDATE institucional_secciones SET imagen=%s WHERE clave=%s",
                            (imagen_url, clave)
                        )
                    except Exception as ins_img_err:
                        print(f"Error guardando imagen inicial para {clave}: {ins_img_err}")
            db.commit()
            flash(('Sección "Quiénes Somos"' if clave=='quienes_somos' else 'Sección "Nuestros Valores"') + ' actualizada', 'success')
            return redirect(url_for('admin.nosotros_quienes_somos'))
        except Exception as e:
            db.rollback()
            print(f"Error actualizando sección: {e}")
            flash('Error al actualizar la sección', 'error')

    # GET: asegurar existencia y cargar valores
    seed_nosotros_sections(cursor)
    cursor.execute("SELECT * FROM institucional_secciones WHERE clave=%s", ('quienes_somos',))
    seccion_qs = cursor.fetchone()
    cursor.execute("SELECT * FROM institucional_secciones WHERE clave=%s", ('valores',))
    seccion_valores = cursor.fetchone()
    return render_template('admin/quienes_somos.html', seccion_qs=seccion_qs, seccion_valores=seccion_valores)

# Rutas para gestión de preguntas del quiz
@admin_bp.route('/quiz')
@login_required
def quiz():
    """Gestión de preguntas del quiz"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("SELECT * FROM quiz_preguntas ORDER BY orden, id")
        
        preguntas = cursor.fetchall()
        
        # Convertir a lista de diccionarios para facilitar el manejo en el template
        preguntas_list = []
        for pregunta in preguntas:
            preguntas_list.append({
                    'id': pregunta['id'],
                    'pregunta': pregunta['pregunta'],
                    'opcion_a': pregunta['opcion_a'],
                    'opcion_b': pregunta['opcion_b'],
                    'opcion_c': pregunta['opcion_c'],
                    'respuesta_correcta': pregunta['respuesta_correcta'],
                    'explicacion': pregunta['explicacion'],
                    'orden': pregunta['orden'],
                    'activo': pregunta['activo'],
                    'fecha_creacion': pregunta['fecha_creacion']
                })
        
        return render_template('admin/quiz.html', preguntas=preguntas_list)
        
    except Exception as e:
        print(f"Error al obtener preguntas del quiz: {e}")
        flash('Error al cargar las preguntas del quiz', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/quiz/nueva', methods=['GET', 'POST'])
@login_required
def nueva_pregunta():
    """Crear nueva pregunta del quiz"""
    if request.method == 'POST':
        try:
            pregunta = request.form.get('pregunta')
            opcion_a = request.form.get('opcion_a')
            opcion_b = request.form.get('opcion_b')
            opcion_c = request.form.get('opcion_c')
            respuesta_correcta = request.form.get('respuesta_correcta')
            explicacion = request.form.get('explicacion')
            orden = request.form.get('orden', 1)
            activo = True if request.form.get('activo') else 0
            
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                    INSERT INTO quiz_preguntas (pregunta, opcion_a, opcion_b, opcion_c, respuesta_correcta, explicacion, orden, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (pregunta, opcion_a, opcion_b, opcion_c, respuesta_correcta, explicacion, orden, activo))
            
            db.commit()
            flash('Pregunta creada exitosamente', 'success')
            return redirect(url_for('admin.quiz'))
            
        except Exception as e:
            print(f"Error creando pregunta: {e}")
            flash('Error al crear la pregunta', 'error')
    
    return render_template('admin/quiz_form.html')

def reprocess_product_image(firebase_url, categoria=None):
    """Reprocesar una imagen existente en Firebase Storage con optimización específica por categoría"""
    if not firebase_url or not is_firebase_available():
        return False
    
    try:
        import requests
        from io import BytesIO
        
        # Descargar imagen desde Firebase
        response = requests.get(firebase_url)
        if response.status_code != 200:
            return False
        
        # Usar la nueva función de optimización por categoría
        from firebase_storage import FirebaseStorageManager
        storage_manager = FirebaseStorageManager()
        
        # Aplicar optimización específica por categoría
        if categoria:
            optimized_data = storage_manager._optimize_product_image_by_category(response.content, categoria)
            print(f"Aplicando optimización específica para categoría: {categoria}")
        else:
            # Fallback a optimización estándar si no hay categoría
            optimized_data = storage_manager._optimize_image(response.content)
            print("Aplicando optimización estándar (sin categoría especificada)")
        
        # Crear un archivo temporal en memoria con los datos optimizados
        img_buffer = BytesIO(optimized_data)
        
        # Crear un objeto de archivo simulado para upload_file
        from werkzeug.datastructures import FileStorage
        temp_file = FileStorage(
            stream=img_buffer,
            filename='reprocessed_image.jpg',
            content_type='image/jpeg'
        )
        
        # Subir imagen reprocesada a Firebase (reemplazará la existente)
        # No aplicar optimización adicional ya que ya fue optimizada específicamente por categoría
        new_url = upload_file(temp_file, folder='productos', optimize_image=False)
        
        # Eliminar la imagen original de Firebase si la nueva subida fue exitosa
        if new_url and new_url != firebase_url:
            delete_file(firebase_url)
            return new_url
        
        return firebase_url if new_url else False
            
    except Exception as e:
        print(f"Error reprocesando imagen {image_filename}: {e}")
        return False

@admin_bp.route('/reprocess-images')
@login_required
def reprocess_images():
    """Reprocesar todas las imágenes de productos para asegurar tamaño correcto"""
    try:
        if not is_firebase_available():
            flash('Firebase Storage no está disponible', 'error')
            return redirect(url_for('admin.productos'))
        
        db = get_db()
        cursor = db.cursor()
        
        # Obtener todos los productos con imágenes
        cursor.execute("SELECT id, nombre, imagen, categoria FROM productos WHERE imagen IS NOT NULL AND imagen != ''")
        productos = cursor.fetchall()
        
        if not productos:
            flash('No se encontraron productos con imágenes para reprocesar', 'info')
            return redirect(url_for('admin.productos'))
        
        processed_count = 0
        updated_count = 0
        
        # Reprocesar cada imagen
        for producto in productos:
            producto_id = producto['id'] if isinstance(producto, dict) else producto[0]
            producto_nombre = producto['nombre'] if isinstance(producto, dict) else producto[1]
            imagen_url = producto['imagen'] if isinstance(producto, dict) else producto[2]
            categoria = producto['categoria'] if isinstance(producto, dict) else producto[3]
            
            # Solo procesar URLs de Firebase
            if imagen_url and imagen_url.startswith('https://'):
                print(f"Reprocesando imagen del producto: {producto_nombre} (Categoría: {categoria})")
                result = reprocess_product_image(imagen_url, categoria)
                
                if result and result != imagen_url:
                    # Actualizar la URL en la base de datos
                    cursor.execute("UPDATE productos SET imagen = %s WHERE id = %s", (result, producto_id))
                    updated_count += 1
                    print(f"Imagen actualizada para {producto_nombre}: {result}")
                elif result:
                    print(f"Imagen reprocesada para {producto_nombre} (misma URL)")
                
                processed_count += 1
            else:
                print(f"Saltando imagen local para {producto_nombre}: {imagen_url}")
        
        # Confirmar cambios en la base de datos
        if updated_count > 0:
            db.commit()
        
        if processed_count > 0:
            flash(f'Se reprocesaron {processed_count} imágenes exitosamente. {updated_count} URLs actualizadas.', 'success')
        else:
            flash('No se encontraron imágenes de Firebase para reprocesar', 'info')
        
    except Exception as e:
        print(f"Error reprocesando imágenes: {e}")
        flash('Error al reprocesar las imágenes', 'error')
    
    return redirect(url_for('admin.productos'))

@admin_bp.route('/quiz/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_pregunta(id):
    """Editar pregunta del quiz"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        if request.method == 'POST':
            pregunta = request.form.get('pregunta')
            opcion_a = request.form.get('opcion_a')
            opcion_b = request.form.get('opcion_b')
            opcion_c = request.form.get('opcion_c')
            respuesta_correcta = request.form.get('respuesta_correcta')
            explicacion = request.form.get('explicacion')
            orden = request.form.get('orden', 1)
            activo = True if request.form.get('activo') else 0
            
            cursor.execute("""
                    UPDATE quiz_preguntas 
                    SET pregunta=%s, opcion_a=%s, opcion_b=%s, opcion_c=%s, respuesta_correcta=%s, explicacion=%s, orden=%s, activo=%s
                    WHERE id=%s
                """, (pregunta, opcion_a, opcion_b, opcion_c, respuesta_correcta, explicacion, orden, activo, id))
            
            db.commit()
            flash('Pregunta actualizada exitosamente', 'success')
            return redirect(url_for('admin.quiz'))
        
        # GET - Obtener datos de la pregunta
        cursor.execute("SELECT * FROM quiz_preguntas WHERE id = %s", (id,))
        
        pregunta_data = cursor.fetchone()
        
        if not pregunta_data:
            flash('Pregunta no encontrada', 'error')
            return redirect(url_for('admin.quiz'))
        
        # Convertir a diccionario
        pregunta = {
                'id': pregunta_data['id'],
                'pregunta': pregunta_data['pregunta'],
                'opcion_a': pregunta_data['opcion_a'],
                'opcion_b': pregunta_data['opcion_b'],
                'opcion_c': pregunta_data['opcion_c'],
                'respuesta_correcta': pregunta_data['respuesta_correcta'],
                'explicacion': pregunta_data['explicacion'],
                'orden': pregunta_data['orden'],
                'activo': pregunta_data['activo']
            }
        
        return render_template('admin/quiz_form.html', pregunta=pregunta)
        
    except Exception as e:
        print(f"Error al editar pregunta: {e}")
        flash('Error al editar la pregunta', 'error')
        return redirect(url_for('admin.quiz'))

@admin_bp.route('/quiz/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_pregunta(id):
    """Eliminar pregunta del quiz"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM quiz_preguntas WHERE id = %s", (id,))
        
        db.commit()
        flash('Pregunta eliminada exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al eliminar pregunta: {e}")
        flash('Error al eliminar la pregunta', 'error')
    
    return redirect(url_for('admin.quiz'))

# ==================== RUTAS DEL CHATBOT ====================

@admin_bp.route('/chatbot')
@login_required
def chatbot():
    """Gestión del chatbot TanquiBot"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener preguntas del chatbot
        cursor.execute("""
                SELECT id, pregunta, respuesta, palabras_clave, categoria, activo, orden, fecha_creacion
                FROM chatbot_preguntas 
                ORDER BY orden ASC, id DESC
            """)
        
        preguntas = cursor.fetchall()
        
        # Obtener configuración del chatbot
        cursor.execute("SELECT * FROM chatbot_configuracion WHERE id = %s", (1,))
        configuracion = cursor.fetchone()
        
        # Si no hay configuración, crear una por defecto
        if not configuracion:
            cursor.execute('''
                INSERT INTO chatbot_configuracion (id, nombre_bot, mensaje_bienvenida, mensaje_no_entendido, activo, usar_gpt)
                VALUES (1, 'TanquiBot', 
                        '¡Hola! 👋 Soy TanquiBot, tu asistente virtual de DH2OCOL. Estoy aquí para ayudarte con información sobre nuestros servicios de tanques de agua. ¿En qué puedo ayudarte hoy?', 
                        'Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles? También puedes contactarnos directamente por WhatsApp.', 
                        TRUE, FALSE)
            ''')
            db.commit()
            
            # Obtener la configuración recién creada
            cursor.execute("SELECT * FROM chatbot_configuracion WHERE id = %s", (1,))
            configuracion = cursor.fetchone()
        
        return render_template('admin/chatbot.html', 
                             preguntas=preguntas, 
                             configuracion=configuracion)
        
    except Exception as e:
        print(f"Error al cargar chatbot: {e}")
        flash('Error al cargar la configuración del chatbot', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/chatbot/nueva-pregunta', methods=['POST'])
@login_required
def nueva_pregunta_chatbot():
    """Agregar nueva pregunta al chatbot"""
    try:
        pregunta = request.form.get('pregunta', '').strip()
        respuesta = request.form.get('respuesta', '').strip()
        activo = True if request.form.get('activo') else 0
        
        if not pregunta or not respuesta:
            flash('La pregunta y respuesta son obligatorias', 'error')
            return redirect(url_for('admin.chatbot'))
        
        db = get_db()
        cursor = db.cursor()
        
        # Insertar nueva pregunta
        cursor.execute("""
            INSERT INTO chatbot_preguntas (pregunta, respuesta, activo)
            VALUES (%s, %s, %s)
        """, (pregunta, respuesta, activo))
        
        db.commit()
        flash('Pregunta agregada exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al agregar pregunta: {e}")
        flash('Error al agregar la pregunta', 'error')
    
    return redirect(url_for('admin.chatbot'))

# ==================== FUNCIONALIDAD DE RESTABLECIMIENTO DE CONTRASEÑAS ====================

@admin_bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """Solicitar restablecimiento de contraseña"""
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            
            if not username or not email:
                flash('Todos los campos son obligatorios', 'error')
                return render_template('admin/reset_password_request.html')
            
            db = get_db()
            cursor = db.cursor()
            
            # Verificar si el usuario existe
            cursor.execute("SELECT id, email FROM usuarios WHERE username = %s AND email = %s", (username, email))
            
            user = cursor.fetchone()
            
            if not user:
                flash('Usuario o email no encontrado', 'error')
                return render_template('admin/reset_password_request.html')
            
            # Generar token de restablecimiento
            import secrets
            import datetime
            
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=1)  # Token válido por 1 hora
            
            # Guardar token en la base de datos
            cursor.execute("""
                    INSERT INTO password_reset_tokens (user_id, token, expires_at, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE token = VALUES(token), expires_at = VALUES(expires_at), created_at = VALUES(created_at)
                """, (user[0], reset_token, expires_at, datetime.datetime.now()))
            
            db.commit()
            
            # Enviar email con el token
            from email_utils import send_password_reset_email
            
            email_sent = send_password_reset_email(user[1], reset_token, username)
            
            if not email_sent:
                flash('Error al enviar el email. Verifica la configuración de correo.', 'error')
                return render_template('admin/reset_password_request.html')
            flash('Se ha enviado un enlace de restablecimiento a tu email', 'success')
            return redirect(url_for('admin.login'))
            
        except Exception as e:
            print(f"Error al solicitar restablecimiento: {e}")
            flash('Error al procesar la solicitud', 'error')
    
    return render_template('admin/reset_password_request.html')

@admin_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Restablecer contraseña con token"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verificar token válido
        cursor.execute("""
                SELECT prt.user_id, u.username 
                FROM password_reset_tokens prt
                JOIN usuarios u ON prt.user_id = u.id
                WHERE prt.token = %s AND prt.expires_at > NOW()
            """, (token,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            flash('Token inválido o expirado', 'error')
            return redirect(url_for('admin.login'))
        
        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not new_password or not confirm_password:
                flash('Todos los campos son obligatorios', 'error')
                return render_template('admin/reset_password.html', token=token)
            
            if new_password != confirm_password:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('admin/reset_password.html', token=token)
            
            if len(new_password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'error')
                return render_template('admin/reset_password.html', token=token)
            
            # Actualizar contraseña
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(new_password)
            
            cursor.execute("UPDATE usuarios SET password = %s WHERE id = %s", (hashed_password, user_data[0]))
            cursor.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
            
            db.commit()
            flash('Contraseña actualizada exitosamente', 'success')
            return redirect(url_for('admin.login'))
        
        return render_template('admin/reset_password.html', token=token, username=user_data[1])
        
    except Exception as e:
        print(f"Error al restablecer contraseña: {e}")
        flash('Error al procesar la solicitud', 'error')
        return redirect(url_for('admin.login'))

@admin_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña desde el panel de administración"""
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not current_password or not new_password or not confirm_password:
                flash('Todos los campos son obligatorios', 'error')
                return render_template('admin/change_password.html')
            
            if new_password != confirm_password:
                flash('Las contraseñas nuevas no coinciden', 'error')
                return render_template('admin/change_password.html')
            
            if len(new_password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'error')
                return render_template('admin/change_password.html')
            
            db = get_db()
            cursor = db.cursor()
            
            # Verificar contraseña actual
            user_id = session.get('admin_user_id')
            cursor.execute("SELECT password FROM usuarios WHERE id = %s", (user_id,))
            
            user = cursor.fetchone()
            
            if not user:
                flash('Usuario no encontrado', 'error')
                return render_template('admin/change_password.html')
            
            from werkzeug.security import check_password_hash, generate_password_hash
            
            if not check_password_hash(user[0], current_password):
                flash('Contraseña actual incorrecta', 'error')
                return render_template('admin/change_password.html')
            
            # Actualizar contraseña
            hashed_password = generate_password_hash(new_password)
            
            cursor.execute("UPDATE usuarios SET password = %s WHERE id = %s", (hashed_password, user_id))
            
            db.commit()
            flash('Contraseña cambiada exitosamente', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            print(f"Error al cambiar contraseña: {e}")
            flash('Error al cambiar la contraseña', 'error')
    
    return render_template('admin/change_password.html')

@admin_bp.route('/chatbot/editar-pregunta/<int:pregunta_id>', methods=['POST'])
@login_required
def editar_pregunta_chatbot(pregunta_id):
    """Editar pregunta del chatbot"""
    try:
        pregunta = request.form.get('pregunta', '').strip()
        respuesta = request.form.get('respuesta', '').strip()
        activo = True if request.form.get('activo') else 0
        
        if not pregunta or not respuesta:
            flash('La pregunta y respuesta son obligatorias', 'error')
            return redirect(url_for('admin.chatbot'))
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
                UPDATE chatbot_preguntas 
                SET pregunta = %s, respuesta = %s, activo = %s
                WHERE id = %s
            """, (pregunta, respuesta, activo, pregunta_id))
        
        db.commit()
        flash('Pregunta actualizada exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al editar pregunta: {e}")
        flash('Error al editar la pregunta', 'error')
    
    return redirect(url_for('admin.chatbot'))

@admin_bp.route('/chatbot/eliminar-pregunta/<int:pregunta_id>', methods=['POST'])
@login_required
def eliminar_pregunta_chatbot(pregunta_id):
    """Eliminar pregunta del chatbot"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM chatbot_preguntas WHERE id = %s", (pregunta_id,))
        
        db.commit()
        flash('Pregunta eliminada exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al eliminar pregunta: {e}")
        flash('Error al eliminar la pregunta', 'error')
    
    return redirect(url_for('admin.chatbot'))

@admin_bp.route('/chatbot/toggle-pregunta/<int:pregunta_id>', methods=['POST'])
@login_required
def toggle_pregunta_chatbot(pregunta_id):
    """Activar/desactivar pregunta del chatbot"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("UPDATE chatbot_preguntas SET activo = NOT activo WHERE id = %s", (pregunta_id,))
        
        db.commit()
        flash('Estado de la pregunta actualizado', 'success')
        
    except Exception as e:
        print(f"Error al cambiar estado: {e}")
        flash('Error al cambiar el estado de la pregunta', 'error')
    
    return redirect(url_for('admin.chatbot'))

@admin_bp.route('/chatbot/configuracion', methods=['POST'])
@login_required
def configuracion_chatbot():
    """Actualizar configuración del chatbot"""
    try:
        nombre_bot = request.form.get('nombre_bot', '').strip()
        mensaje_bienvenida = request.form.get('mensaje_bienvenida', '').strip()
        mensaje_no_entendido = request.form.get('mensaje_no_entendido', '').strip()
        recaptcha_site_key = request.form.get('recaptcha_site_key', '').strip()
        recaptcha_secret_key = request.form.get('recaptcha_secret_key', '').strip()
        openai_api_key = request.form.get('openai_api_key', '').strip()
        usar_gpt = 1 if request.form.get('usar_gpt') else 0
        
        if not nombre_bot or not mensaje_bienvenida or not mensaje_no_entendido:
            flash('Todos los campos de configuración son obligatorios', 'error')
            return redirect(url_for('admin.chatbot'))
        
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
                UPDATE chatbot_configuracion 
                SET nombre_bot = %s, mensaje_bienvenida = %s, mensaje_no_entendido = %s,
                    recaptcha_site_key = %s, recaptcha_secret_key = %s,
                    openai_api_key = %s, usar_gpt = %s
                WHERE id = %s
            """, (nombre_bot, mensaje_bienvenida, mensaje_no_entendido, 
                  recaptcha_site_key, recaptcha_secret_key, openai_api_key, usar_gpt, 1))
        
        db.commit()
        flash('Configuración del chatbot actualizada exitosamente', 'success')
        
    except Exception as e:
        print(f"Error al actualizar configuración: {e}")
        flash('Error al actualizar la configuración del chatbot', 'error')
    
    return redirect(url_for('admin.chatbot'))