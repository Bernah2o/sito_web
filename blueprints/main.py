from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app, g
import os
import requests
from openai import OpenAI

main_bp = Blueprint('main', __name__)

def get_db():
    """Obtener conexión a la base de datos"""
    return current_app.get_db()

@main_bp.route('/')
def index():
    """Página de inicio moderna con todo el contenido"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener todos los servicios activos
        cursor.execute("SELECT * FROM servicios WHERE activo = TRUE ORDER BY nombre")
        servicios = cursor.fetchall()
        
        # Obtener todos los productos activos agrupados por categoría
        cursor.execute("SELECT * FROM productos WHERE activo = TRUE ORDER BY categoria, nombre")
        productos_raw = cursor.fetchall()
        
        # Obtener testimonios
        cursor.execute("SELECT * FROM testimonios WHERE activo = TRUE ORDER BY id DESC")
        testimonios = cursor.fetchall()
        
        # Obtener configuración de la empresa
        cursor.execute("SELECT clave, valor FROM configuracion")
        config_raw = cursor.fetchall()
        
        # Obtener imágenes del carrusel
        cursor.execute("SELECT * FROM medios WHERE categoria = 'carousel' ORDER BY fecha_subida DESC")
        carousel_images = cursor.fetchall()
        
        # Agrupar productos por categoría
        productos = {}
        for producto in productos_raw:
            categoria = producto['categoria'] if isinstance(producto, dict) else producto[4]
            if categoria not in productos:
                productos[categoria] = []
            productos[categoria].append(producto)
        
        # Convertir configuración a diccionario
        configuracion = {}
        for config in config_raw:
            clave = config['clave'] if isinstance(config, dict) else config[0]
            valor = config['valor'] if isinstance(config, dict) else config[1]
            configuracion[clave] = valor
        
        return render_template('sitio/inicio.html', 
                             servicios=servicios, 
                             productos=productos, 
                             testimonios=testimonios,
                             configuracion=configuracion,
                             carousel_images=carousel_images)
    except Exception as e:
        print(f"Error al cargar página de inicio: {e}")
        return render_template('sitio/inicio.html', 
                             servicios=[], 
                             productos={}, 
                             testimonios=[],
                             configuracion={},
                             carousel_images=[])

# Nuevas páginas solicitadas

@main_bp.route('/blog-mantenimiento-tanques-agua/')
def blog_mantenimiento():
    """Blog sobre mantenimiento de tanques de agua en Valledupar"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener configuración de la empresa
        cursor.execute("SELECT clave, valor FROM configuracion")
        config_raw = cursor.fetchall()
        
        # Convertir configuración a diccionario
        configuracion = {}
        for config in config_raw:
            clave = config['clave'] if isinstance(config, dict) else config[0]
            valor = config['valor'] if isinstance(config, dict) else config[1]
            configuracion[clave] = valor
        
        return render_template('sitio/blog_mantenimiento.html', configuracion=configuracion)
    except Exception as e:
        print(f"Error al cargar configuración: {e}")
        return render_template('sitio/blog_mantenimiento.html', configuracion={})

@main_bp.route('/limpieza-tanques-elevados-valledupar-dh2o-colombia/')
def limpieza_tanques_elevados():
    """Página sobre limpieza de tanques elevados en Valledupar"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener configuración de la empresa
        cursor.execute("SELECT clave, valor FROM configuracion")
        config_raw = cursor.fetchall()
        
        # Convertir configuración a diccionario
        configuracion = {}
        for config in config_raw:
            clave = config['clave'] if isinstance(config, dict) else config[0]
            valor = config['valor'] if isinstance(config, dict) else config[1]
            configuracion[clave] = valor
        
        # Obtener medios (imágenes y videos) para la galería
        cursor.execute("SELECT * FROM medios WHERE tipo IN ('image', 'video') ORDER BY fecha_subida DESC")
        medios_raw = cursor.fetchall()
        
        # Convertir medios a lista de diccionarios
        medios = []
        for medio in medios_raw:
            medio_dict = {
                    'id': medio['id'],
                    'nombre': medio['nombre'],
                    'filename': medio['filename'],
                    'tipo': medio['tipo'],
                    'descripcion': medio['descripcion'] if 'descripcion' in medio else '',
                    'ruta': medio['ruta'] if 'ruta' in medio else f'uploads/{medio["filename"]}'
                }
            medios.append(medio_dict)
        
        return render_template('sitio/limpieza_tanques_elevados.html', configuracion=configuracion, medios=medios)
    except Exception as e:
        print(f"Error al cargar configuración y medios: {e}")
        return render_template('sitio/limpieza_tanques_elevados.html', configuracion={}, medios=[])

@main_bp.route('/accesorios-tanques-elevados/')
def accesorios_tanques():
    """Página de accesorios y productos para tanques elevados"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener todos los productos activos agrupados por categoría
        cursor.execute("SELECT * FROM productos WHERE activo = TRUE ORDER BY categoria, nombre")
        
        productos_raw = cursor.fetchall()
        
        # Agrupar productos por categoría
        productos_por_categoria = {}
        for producto in productos_raw:
            categoria = producto['categoria']
            if categoria not in productos_por_categoria:
                productos_por_categoria[categoria] = []
            productos_por_categoria[categoria].append(producto)
        
        # Obtener medios de la categoría accesorios
        cursor.execute("SELECT * FROM medios WHERE categoria = 'accesorios' ORDER BY fecha_subida DESC")
        medios_raw = cursor.fetchall()
        
        # Procesar medios para la plantilla
        medios = []
        for medio in medios_raw:
            if isinstance(medio, dict):
                medio_dict = {
                    'id': medio['id'],
                    'titulo': medio.get('nombre', ''),
                    'descripcion': medio.get('descripcion', ''),
                    'ruta': medio.get('ruta', '')
                }
            medios.append(medio_dict)
        
        # Obtener configuración de la empresa
        cursor.execute("SELECT clave, valor FROM configuracion")
        config_raw = cursor.fetchall()
        
        # Convertir configuración a diccionario
        configuracion = {}
        for config in config_raw:
            clave = config['clave'] if isinstance(config, dict) else config[0]
            valor = config['valor'] if isinstance(config, dict) else config[1]
            configuracion[clave] = valor
        
        return render_template('sitio/accesorios_tanques_elevados.html', 
                             productos_por_categoria=productos_por_categoria,
                             configuracion=configuracion,
                             medios=medios)
        
    except Exception as e:
        print(f"Error en accesorios: {e}")
        return render_template('sitio/accesorios_tanques_elevados.html', 
                             productos_por_categoria={},
                             configuracion={},
                             medios=[])


@main_bp.route('/educagua-dh2o-educacion-agua-potable-valledupar/')
def educagua():
    """Página educativa sobre agua potable - EducAgua DH2O"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener preguntas activas del quiz ordenadas
        cursor.execute("SELECT * FROM quiz_preguntas WHERE activo = TRUE ORDER BY orden, id")
        
        preguntas_data = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        preguntas = []
        for pregunta in preguntas_data:
            preguntas.append({
                    'id': pregunta['id'],
                    'pregunta': pregunta['pregunta'],
                    'opcion_a': pregunta['opcion_a'],
                    'opcion_b': pregunta['opcion_b'],
                    'opcion_c': pregunta['opcion_c'],
                    'respuesta_correcta': pregunta['respuesta_correcta'],
                    'explicacion': pregunta['explicacion'],
                    'orden': pregunta['orden']
                })
        
        # Obtener configuración de la empresa
        cursor.execute("SELECT clave, valor FROM configuracion")
        config_raw = cursor.fetchall()
        
        # Convertir configuración a diccionario
        configuracion = {}
        for config in config_raw:
            clave = config['clave'] if isinstance(config, dict) else config[0]
            valor = config['valor'] if isinstance(config, dict) else config[1]
            configuracion[clave] = valor
        
        return render_template('sitio/educagua.html', preguntas=preguntas, configuracion=configuracion)
        
    except Exception as e:
        print(f"Error al cargar preguntas del quiz: {e}")
        # En caso de error, usar preguntas por defecto
        preguntas_default = [
            {
                'id': 1,
                'pregunta': '¿Cada cuánto tiempo se debe limpiar un tanque de agua potable%s',
                'opcion_a': 'Cada 6 meses',
                'opcion_b': 'Cada año',
                'opcion_c': 'Cada 2 años',
                'respuesta_correcta': 'a',
                'explicacion': 'Los tanques de agua potable deben limpiarse cada 6 meses para garantizar la calidad del agua.',
                'orden': 1
            },
            {
                'id': 2,
                'pregunta': '¿Cuál es la capacidad recomendada de un tanque para una familia de 4 personas%s',
                'opcion_a': '500 litros',
                'opcion_b': '1000 litros',
                'opcion_c': '1500 litros',
                'respuesta_correcta': 'b',
                'explicacion': 'Para una familia de 4 personas se recomienda un tanque de 1000 litros.',
                'orden': 2
            },
            {
                'id': 3,
                'pregunta': '¿Qué material es más recomendable para tanques de agua potable%s',
                'opcion_a': 'Concreto',
                'opcion_b': 'Polietileno',
                'opcion_c': 'Metal galvanizado',
                'respuesta_correcta': 'b',
                'explicacion': 'El polietileno es el material más recomendable para tanques de agua potable.',
                'orden': 3
            }
        ]
        return render_template('sitio/educagua.html', preguntas=preguntas_default, configuracion={})

# Redirecciones a redes sociales y aplicación
@main_bp.route('/facebook')
def redirect_facebook():
    """Redirección a Facebook"""
    return redirect('https://www.facebook.com/dh2ocol/', code=301)

@main_bp.route('/youtube')
def redirect_youtube():
    """Redirección a YouTube"""
    return redirect('https://www.youtube.com/channel/UCB0AwlxNPFnN5TeDyfNEHZQ', code=301)

@main_bp.route('/instagram')
def redirect_instagram():
    """Redirección a Instagram"""
    return redirect('https://www.instagram.com/dh2ocol', code=301)

@main_bp.route('/whatsapp')
def redirect_whatsapp():
    """Redirección a WhatsApp"""
    return redirect('https://api.whatsapp.com/message/F6MZTY5TX4F4C1%sautoload=1&app_absent=0', code=301)

@main_bp.route('/tiktok')
def redirect_tiktok():
    """Redirección a TikTok"""
    return redirect('https://www.tiktok.com/@dh2ocol', code=301)

@main_bp.route('/app')
def redirect_app():
    """Redirección a la aplicación DH2O"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave = 'app_url'")
        result = cursor.fetchone()
        app_url = result[0] if result else 'https://app.dh2o.com.co/login/'
        return redirect(app_url, code=301)
    except Exception as e:
        print(f"Error al obtener URL de la app: {e}")
        return redirect('https://app.dh2o.com.co/login/', code=301)

@main_bp.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        empresa = request.form.get('empresa')
        mensaje = request.form.get('mensaje')
        
        # Validar datos básicos
        if not all([nombre, email, mensaje]):
            flash('Por favor completa todos los campos obligatorios', 'error')
            return redirect(url_for('main.index') + '#contacto')
        
        try:
            # Insertar en la base de datos
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                    INSERT INTO contactos (nombre, email, telefono, empresa, mensaje, estado)
                    VALUES (%s, %s, %s, %s, %s, 'nuevo')
                """, (nombre, email, telefono, empresa, mensaje))
            
            db.commit()
            
            # Enviar emails de notificación
            from email_utils import send_contact_email
            email_sent = send_contact_email(nombre, email, telefono, empresa, mensaje)
            
            if email_sent:
                flash('¡Mensaje enviado exitosamente! Te contactaremos pronto. También hemos enviado una confirmación a tu email.', 'success')
            else:
                flash('¡Mensaje enviado exitosamente! Te contactaremos pronto. (Nota: No se pudo enviar la confirmación por email)', 'warning')
            
            return redirect(url_for('main.index') + '#contacto')
            
        except Exception as e:
            print(f"Error al guardar contacto: {e}")
            flash('Error al enviar el mensaje. Inténtalo nuevamente.', 'error')
            return redirect(url_for('main.index') + '#contacto')
    
    # For GET requests, redirect to main page contact section
    return redirect(url_for('main.index') + '#contacto')

@main_bp.route('/descargar-politica')
def descargar_politica():
    """Descargar política de tratamiento de datos"""
    try:
        pdf_path = os.path.join(current_app.root_path, 'static', 'pdf', 'politica-tratamiento-datos.pdf')
        return send_file(pdf_path, as_attachment=True, download_name='politica-tratamiento-datos.pdf')
    except FileNotFoundError:
        flash('Archivo no encontrado', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/api/cotizar', methods=['POST'])
def cotizar_servicio():
    """API para cotización de servicios"""
    try:
        data = request.get_json()
        tipo_servicio = data.get('tipo_servicio')
        cantidad_tanques = int(data.get('cantidad_tanques', 1))
        
        # Obtener precio del servicio desde la base de datos
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("SELECT precio_base FROM servicios WHERE nombre LIKE %s AND activo = TRUE", 
                      (f'%{tipo_servicio}%',))
        servicio = cursor.fetchone()
        
        if servicio:
            precio_base = float(servicio['precio_base'] if isinstance(servicio, dict) else servicio[0])
        else:
            # Precios por defecto si no se encuentra en la BD
            precios_base = {
                'limpieza': 150000,
                'reparacion': 200000,
                'instalacion': 500000,
                'mantenimiento': 100000
            }
            precio_base = precios_base.get(tipo_servicio, 150000)
        
        precio_total = precio_base * cantidad_tanques
        
        # Descuentos por volumen
        descuento_aplicado = 0
        if cantidad_tanques >= 5:
            descuento_aplicado = 10
            precio_total *= 0.9  # 10% descuento
        elif cantidad_tanques >= 3:
            descuento_aplicado = 5
            precio_total *= 0.95  # 5% descuento
        
        return jsonify({
            'success': True,
            'precio_total': precio_total,
            'precio_unitario': precio_base,
            'cantidad': cantidad_tanques,
            'descuento_aplicado': descuento_aplicado
        })
        
    except Exception as e:
        print(f"Error en cotización: {e}")
        return jsonify({
            'success': False,
            'error': 'Error al calcular cotización'
        }), 400

# ===== RUTAS DEL CHATBOT API =====

@main_bp.route('/api/chatbot/opciones-rapidas')
def chatbot_opciones_rapidas():
    """Obtener opciones rápidas del chatbot"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener las primeras 4 preguntas más populares
        cursor.execute("""
                SELECT pregunta, respuesta 
                FROM chatbot_preguntas 
                WHERE activo = TRUE 
                ORDER BY orden ASC 
                LIMIT 4
            """)
        
        opciones = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        opciones_list = []
        for opcion in opciones:
            opciones_list.append({
                'pregunta': opcion['pregunta'] if isinstance(opcion, dict) else opcion[0],
                'respuesta': opcion['respuesta'] if isinstance(opcion, dict) else opcion[1]
            })
        
        return jsonify(opciones_list)
        
    except Exception as e:
        print(f"Error obteniendo opciones rápidas: {e}")
        return jsonify([])

def verificar_recaptcha(token):
    """Verificar token de reCAPTCHA"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Obtener clave secreta de reCAPTCHA
        cursor.execute("SELECT recaptcha_secret_key FROM chatbot_configuracion WHERE activo = TRUE LIMIT 1")
        
        config = cursor.fetchone()
        if not config:
            return False
            
        secret_key = config['recaptcha_secret_key'] if isinstance(config, dict) else config[0]
        if not secret_key:
            return False
        
        # Verificar con Google
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', {
            'secret': secret_key,
            'response': token
        })
        
        result = response.json()
        return result.get('success', False) and result.get('score', 0) > 0.5
        
    except Exception as e:
        print(f"Error verificando reCAPTCHA: {e}")
        return False

@main_bp.route('/api/chatbot/mensaje', methods=['POST'])
def chatbot_mensaje():
    """Procesar mensaje del chatbot"""
    try:
        data = request.get_json()
        mensaje_usuario = data.get('mensaje', '').strip().lower()
        session_id = data.get('session_id', '')
        recaptcha_token = data.get('recaptcha_token', '')
        
        if not mensaje_usuario:
            return jsonify({
                'success': False,
                'mensaje': 'Mensaje vacío'
            }), 400
        
        # Verificar reCAPTCHA si está presente
        if recaptcha_token:
            if not verificar_recaptcha(recaptcha_token):
                return jsonify({
                    'success': False,
                    'mensaje': 'Verificación de seguridad fallida. Por favor, intenta nuevamente.'
                }), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # Buscar respuesta en la base de datos
        respuesta_encontrada = None
        pregunta_id = None
        
        # Buscar por palabras clave
        cursor.execute("""
                SELECT id, pregunta, respuesta, palabras_clave 
                FROM chatbot_preguntas 
                WHERE activo = TRUE
            """)
        
        preguntas = cursor.fetchall()
        
        # Buscar coincidencias
        for pregunta in preguntas:
            pregunta_id_temp = pregunta['id'] if isinstance(pregunta, dict) else pregunta[0]
            pregunta_texto = pregunta['pregunta'] if isinstance(pregunta, dict) else pregunta[1]
            respuesta_texto = pregunta['respuesta'] if isinstance(pregunta, dict) else pregunta[2]
            palabras_clave = pregunta['palabras_clave'] if isinstance(pregunta, dict) else pregunta[3]
            
            # Verificar si alguna palabra clave coincide
            if palabras_clave:
                palabras = [p.strip().lower() for p in palabras_clave.split(',')]
                for palabra in palabras:
                    if palabra in mensaje_usuario:
                        respuesta_encontrada = respuesta_texto
                        pregunta_id = pregunta_id_temp
                        break
                
                if respuesta_encontrada:
                    break
        
        # Si no se encontró respuesta, verificar si usar GPT o mensaje por defecto
        if not respuesta_encontrada:
            # Obtener configuración del chatbot
            cursor.execute("SELECT mensaje_no_entendido, openai_api_key, usar_gpt FROM chatbot_configuracion WHERE activo = TRUE LIMIT 1")
            
            config = cursor.fetchone()
            
            # Intentar usar GPT si está habilitado
            if config and config[2] and config[1]:  # usar_gpt y openai_api_key
                try:
                    client = OpenAI(api_key=config[1])
                    
                    # Crear contexto sobre DH2OCOL
                    contexto = """Eres TanquiBot, el asistente virtual de DH2OCOL, una empresa especializada en:
- Limpieza y mantenimiento de tanques de agua
- Venta de tanques elevados y subterráneos
- Accesorios para tanques de agua
- Servicios de educación sobre agua potable (EducAgua)
- Ubicada en Valledupar, Colombia

Responde de manera amigable y profesional. Si la pregunta no está relacionada con nuestros servicios, 
redirige cortésmente hacia nuestros servicios o sugiere contactar por WhatsApp."""
                    
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": contexto},
                            {"role": "user", "content": data.get('mensaje', '')}
                        ],
                        max_tokens=200,
                        temperature=0.7
                    )
                    
                    respuesta_encontrada = response.choices[0].message.content
                    
                except Exception as e:
                    print(f"Error con OpenAI: {e}")
                    # Si falla GPT, usar mensaje por defecto
                    if config:
                        respuesta_encontrada = config[0] if config[0] else "Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles%s También puedes contactarnos directamente por WhatsApp."
                    else:
                        respuesta_encontrada = "Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles%s También puedes contactarnos directamente por WhatsApp."
            else:
                # Usar mensaje por defecto
                if config:
                    respuesta_encontrada = config[0] if config[0] else "Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles%s También puedes contactarnos directamente por WhatsApp."
                else:
                    respuesta_encontrada = "Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles%s También puedes contactarnos directamente por WhatsApp."
        
        # Guardar conversación
        try:
            user_agent = request.headers.get('User-Agent', '')
            ip_usuario = request.remote_addr
            
            cursor.execute("""
                INSERT INTO chatbot_conversaciones 
                (session_id, pregunta_usuario, respuesta_bot, pregunta_id, ip_usuario, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session_id, data.get('mensaje', ''), respuesta_encontrada, pregunta_id, ip_usuario, user_agent))
            
            db.commit()
        except Exception as e:
            print(f"Error guardando conversación: {e}")
        
        return jsonify({
            'success': True,
            'respuesta': respuesta_encontrada
        })
        
    except Exception as e:
        print(f"Error procesando mensaje del chatbot: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@main_bp.route('/politica-tratamiento-datos')
def politica_tratamiento_datos():
    """Servir el PDF de Política de Tratamiento de Datos"""
    try:
        # Ruta del archivo PDF
        pdf_path = os.path.join(current_app.root_path, 'Política de tratamiento de datos.pdf')
        
        # Verificar que el archivo existe
        if not os.path.exists(pdf_path):
            flash('El documento de Política de Tratamiento de Datos no está disponible en este momento.', 'error')
            return redirect(url_for('main.index'))
        
        # Servir el archivo PDF
        return send_file(
            pdf_path,
            as_attachment=False,  # Para mostrar en el navegador en lugar de descargar
            download_name='Politica_Tratamiento_Datos_DH2OCOL.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error sirviendo PDF de política: {e}")
        flash('Error al acceder al documento. Inténtalo nuevamente.', 'error')
        return redirect(url_for('main.index'))