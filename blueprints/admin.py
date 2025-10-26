from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import uuid
from datetime import datetime
from PIL import Image, ImageOps
from jwt_utils import JWTManager, admin_required
from firebase_storage import upload_file, delete_file, is_firebase_available

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Configuración para subida de imágenes
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file, categoria):
    """Guardar imagen de producto en Firebase Storage y retornar la URL pública"""
    if not file or not allowed_file(file.filename):
        return None
    
    if not is_firebase_available():
        print("Firebase Storage no está disponible")
        return None
    
    try:
        # Determinar carpeta basada en la categoría
        folder = f"productos/{categoria.lower()}" if categoria else "productos"
        
        # Subir archivo a Firebase Storage con optimización automática
        firebase_url = upload_file(file, folder=folder, optimize_image=True)
        
        if firebase_url:
            print(f"Imagen subida exitosamente a Firebase: {firebase_url}")
            return firebase_url
        else:
            print("Error al subir imagen a Firebase Storage")
            return None
            
    except Exception as e:
        print(f"Error procesando imagen: {e}")
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
                    'size': file_data['tamaño'],
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
                INSERT INTO medios (nombre, filename, tipo, categoria, tamaño, descripcion, ruta)
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
        
        # Eliminar archivo de Firebase Storage si es una URL de Firebase
        if firebase_url and 'firebase' in firebase_url:
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
                
                # Eliminar archivo de Firebase Storage si es una URL de Firebase
                firebase_success = True
                if firebase_url and 'firebase' in firebase_url:
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
                    'size': file_data['tamaño'],
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
            
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                    INSERT INTO servicios (nombre, descripcion, precio_base, activo)
                    VALUES (%s, %s, %s, TRUE)
                """, (nombre, descripcion, precio_base))
            
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
    
    return render_template('admin/nuevo_testimonio.html')



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
            
            db = get_db()
            cursor = db.cursor()
            
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
    """Eliminar producto"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
        
        db.commit()
        flash('Producto eliminado exitosamente', 'success')
        
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
    
    return render_template('admin/quiz.html')

def reprocess_product_image(firebase_url):
    """Reprocesar una imagen existente en Firebase Storage para asegurar el tamaño correcto"""
    if not firebase_url or not is_firebase_available():
        return False
    
    try:
        import requests
        from io import BytesIO
        
        # Descargar imagen desde Firebase
        response = requests.get(firebase_url)
        if response.status_code != 200:
            return False
        
        # Abrir imagen desde bytes
        image = Image.open(BytesIO(response.content))
        
        # Convertir a RGB si es necesario
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Corregir orientación
        image = ImageOps.exif_transpose(image)
        
        # Redimensionar con el mismo proceso que save_product_image
        target_size = (400, 300)
        image.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Crear imagen final con fondo blanco
        final_image = Image.new('RGB', target_size, (255, 255, 255))
        x_offset = (target_size[0] - image.width) // 2
        y_offset = (target_size[1] - image.height) // 2
        final_image.paste(image, (x_offset, y_offset))
        
        # Crear un archivo temporal en memoria
        img_buffer = BytesIO()
        final_image.save(img_buffer, 'JPEG', quality=85, optimize=True)
        img_buffer.seek(0)
        
        # Crear un objeto de archivo simulado para upload_file
        from werkzeug.datastructures import FileStorage
        temp_file = FileStorage(
            stream=img_buffer,
            filename='reprocessed_image.jpg',
            content_type='image/jpeg'
        )
        
        # Subir imagen reprocesada a Firebase (reemplazará la existente)
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
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'productos')
        
        if not os.path.exists(upload_folder):
            flash('No se encontró la carpeta de imágenes', 'error')
            return redirect(url_for('admin.productos'))
        
        # Obtener lista de archivos de imagen
        image_files = [f for f in os.listdir(upload_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        processed_count = 0
        updated_filenames = {}
        
        # Reprocesar cada imagen
        for filename in image_files:
            result = reprocess_product_image(filename)
            if result:
                processed_count += 1
                if result != filename:  # Si cambió el nombre (PNG -> JPG)
                    updated_filenames[filename] = result
        
        # Actualizar base de datos si hay cambios de nombre de archivo
        if updated_filenames:
            db = get_db()
            cursor = db.cursor()
            
            for old_name, new_name in updated_filenames.items():
                cursor.execute("UPDATE productos SET imagen = %s WHERE imagen = %s", (new_name, old_name))
            
            db.commit()
        
        flash(f'Se reprocesaron {processed_count} imágenes exitosamente', 'success')
        
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