from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app, g
import os
import requests
from openai import OpenAI
from flask_mail import Message
from firebase_storage import upload_file, delete_file, is_firebase_available

main_bp = Blueprint('main', __name__)

def get_db():
    """Obtener conexión a la base de datos"""
    return current_app.get_db()

def get_recaptcha_site_key():
    """Obtener la clave pública de reCAPTCHA desde la configuración"""
    return current_app.config.get('RECAPTCHA_SITE_KEY')

@main_bp.app_context_processor
def inject_recaptcha():
    """Inyectar configuración de reCAPTCHA en todos los templates"""
    return {
        'recaptcha_site_key': get_recaptcha_site_key(),
        'wompi_checkout_url': current_app.config.get('WOMPI_CHECKOUT_URL'),
        'nequi_qr_filename': current_app.config.get('NEQUI_QR_FILENAME', 'img/qr_nequi.jpeg'),
        'breb_qr_filename': current_app.config.get('BREB_QR_FILENAME', 'img/qr_negocios.jpeg'),
        'nequi_payment_url': current_app.config.get('NEQUI_PAYMENT_URL'),
        'nequi_phone_number': current_app.config.get('NEQUI_PHONE_NUMBER'),
        'breb_bank_name': current_app.config.get('BREB_BANK_NAME'),
        'breb_account_type': current_app.config.get('BREB_ACCOUNT_TYPE'),
        'breb_account_number': current_app.config.get('BREB_ACCOUNT_NUMBER'),
        'breb_account_holder': current_app.config.get('BREB_ACCOUNT_HOLDER'),
    }

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
        
        # Debug: Log de las URLs del carrusel
        for img in carousel_images:
            print(f"Imagen del carrusel: {img.get('nombre', 'Sin nombre')} - URL: {img.get('ruta', 'Sin URL')}")
        
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
        
        # Obtener medios (imágenes y videos) para la galería, excluyendo las imágenes del carrusel
        cursor.execute("SELECT * FROM medios WHERE tipo IN ('image', 'video') AND categoria != 'carousel' ORDER BY fecha_subida DESC")
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
    from urllib.parse import quote_plus
    # Mensaje predeterminado que aparecerá en el chat
    default_message = (
        "Hola, me gustaría iniciar una conversación con DH2OCOL "
        "para obtener más información. ¡Gracias!"
    )
    wa_url = f"https://wa.me/573157484662?text={quote_plus(default_message)}"
    return redirect(wa_url, code=301)

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
        acepta_politica = request.form.get('acepta_politica')
        recaptcha_token = request.form.get('recaptcha_token')
        
        # Validar datos básicos
        if not all([nombre, email, mensaje]):
            flash('Por favor completa todos los campos obligatorios', 'error')
            return redirect(url_for('main.index') + '#contacto')

        # Validar aceptación de Política de Privacidad
        if not acepta_politica:
            flash('Debes aceptar la Política de Privacidad y Tratamiento de Datos Personales.', 'error')
            return redirect(url_for('main.index') + '#contacto')
        
        # Verificar reCAPTCHA si está configurado
        if recaptcha_token and not verificar_recaptcha(recaptcha_token):
            flash('Error de verificación de seguridad. Inténtalo nuevamente.', 'error')
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
                flash('¡Mensaje enviado exitosamente! Te contactaremos pronto. Hemos enviado una confirmación a tu email.', 'success')
            else:
                flash('¡Mensaje enviado exitosamente! Te contactaremos pronto.', 'success')
            
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
    """Verificar token de reCAPTCHA usando variables de entorno"""
    try:
        # Obtener clave secreta de reCAPTCHA desde variables de entorno
        secret_key = current_app.config.get('RECAPTCHA_SECRET_KEY')
        
        if not secret_key:
            return True  # Si no hay clave secreta configurada, permitir acceso
        
        # Verificar con Google
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', {
            'secret': secret_key,
            'response': token
        })
        
        result = response.json()
        return result.get('success', False) and result.get('score', 0) > 0.5
        
    except Exception as e:
        print(f"Error verificando reCAPTCHA: {e}")
        return True  # En caso de error, permitir acceso

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
            if config and config['usar_gpt'] and config['openai_api_key']:  # usar_gpt y openai_api_key
                try:
                    client = OpenAI(api_key=config['openai_api_key'])
                    
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
                        respuesta_encontrada = config['mensaje_no_entendido'] if config['mensaje_no_entendido'] else "Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles%s También puedes contactarnos directamente por WhatsApp."
                    else:
                        respuesta_encontrada = "Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles%s También puedes contactarnos directamente por WhatsApp."
            else:
                # Usar mensaje por defecto
                if config:
                    respuesta_encontrada = config['mensaje_no_entendido'] if config['mensaje_no_entendido'] else "Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles%s También puedes contactarnos directamente por WhatsApp."
                else:
                    respuesta_encontrada = "Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles%s También puedes contactarnos directamente por WhatsApp."
        
        # Guardar conversación
        try:
            user_agent = request.headers.get('User-Agent', '')
            ip_usuario = request.remote_addr
            
            cursor.execute("""
                INSERT INTO chatbot_conversaciones 
                (session_id, mensaje_usuario, respuesta_bot, ip_usuario, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_id, data.get('mensaje', ''), respuesta_encontrada, ip_usuario, user_agent))
            
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

# === Páginas de Políticas ===

@main_bp.route('/terminos-de-uso')
def terminos_uso():
    """Página de Términos de Uso"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT clave, valor FROM configuracion")
        config_raw = cursor.fetchall()
        configuracion = {}
        for config in config_raw:
            clave = config['clave'] if isinstance(config, dict) else config[0]
            valor = config['valor'] if isinstance(config, dict) else config[1]
            configuracion[clave] = valor
        return render_template('sitio/terminos_uso.html', configuracion=configuracion)
    except Exception as e:
        print(f"Error al cargar Términos de Uso: {e}")
        return render_template('sitio/terminos_uso.html', configuracion={})

@main_bp.route('/politicas-de-privacidad')
def politicas_privacidad():
    """Página de Políticas de Privacidad"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT clave, valor FROM configuracion")
        config_raw = cursor.fetchall()
        configuracion = {}
        for config in config_raw:
            clave = config['clave'] if isinstance(config, dict) else config[0]
            valor = config['valor'] if isinstance(config, dict) else config[1]
            configuracion[clave] = valor
        return render_template('sitio/politicas_privacidad.html', configuracion=configuracion)
    except Exception as e:
        print(f"Error al cargar Políticas de Privacidad: {e}")
        return render_template('sitio/politicas_privacidad.html', configuracion={})

@main_bp.route('/politicas-de-cookies')
def politicas_cookies():
    """Página de Políticas de Cookies"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT clave, valor FROM configuracion")
        config_raw = cursor.fetchall()
        configuracion = {}
        for config in config_raw:
            clave = config['clave'] if isinstance(config, dict) else config[0]
            valor = config['valor'] if isinstance(config, dict) else config[1]
            configuracion[clave] = valor
        return render_template('sitio/politicas_cookies.html', configuracion=configuracion)
    except Exception as e:
        print(f"Error al cargar Políticas de Cookies: {e}")
        return render_template('sitio/politicas_cookies.html', configuracion={})

# ============================
# API: Cotizador (Wizard)
# ============================

@main_bp.route('/api/quote/params', methods=['GET'])
def quote_params():
    """Obtener parámetros de precios desde configuración para permitir ajuste en Admin"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT clave, valor FROM configuracion WHERE clave LIKE 'quote_%'")
        rows = cursor.fetchall()
        params = {}
        for row in rows:
            if isinstance(row, dict):
                params[row['clave']] = row['valor']
            else:
                params[row[0]] = row[1]
        return jsonify({ 'success': True, 'params': params })
    except Exception as e:
        print(f"Error obteniendo parámetros de cotización: {e}")
        return jsonify({ 'success': False, 'message': 'Error de servidor' }), 500

@main_bp.route('/api/quote/upload', methods=['POST'])
def quote_upload():
    """Subir imágenes del wizard a Firebase y devolver URLs públicas"""
    try:
        if not is_firebase_available():
            return jsonify({ 'success': False, 'message': 'Firebase no disponible' }), 503
        files = request.files.getlist('images')
        if not files:
            return jsonify({ 'success': True, 'urls': [] })
        # Usar carpeta de destino (por defecto 'cotizaciones')
        folder = request.form.get('folder') or 'cotizaciones'
        urls = []
        for f in files:
            url = upload_file(f, folder=folder, optimize_image=True)
            if url:
                urls.append(url)
        return jsonify({ 'success': True, 'urls': urls })
    except Exception as e:
        print(f"Error subiendo imágenes de cotización: {e}")
        return jsonify({ 'success': False, 'message': 'Error al subir imágenes' }), 500

@main_bp.route('/api/quote/delete', methods=['POST'])
def quote_delete():
    """Eliminar una imagen subida a Firebase (por URL pública)"""
    try:
        if not is_firebase_available():
            return jsonify({ 'success': False, 'message': 'Firebase no disponible' }), 503
        data = request.get_json() or {}
        url = data.get('url') or ''
        if not url:
            return jsonify({ 'success': False, 'message': 'URL requerida' }), 400
        ok = delete_file(url)
        return jsonify({ 'success': bool(ok) })
    except Exception as e:
        print(f"Error eliminando imagen de cotización: {e}")
        return jsonify({ 'success': False, 'message': 'Error al eliminar imagen' }), 500

@main_bp.route('/api/quote/email', methods=['POST'])
def quote_email():
    """Enviar correo con resumen de cotización y adjuntar imágenes si hay URLs"""
    try:
        data = request.get_json() or {}
        servicio = data.get('servicio')
        datos = data.get('datos', {})
        estimate = data.get('estimate', {})
        image_urls = data.get('image_urls', [])
        recaptcha_token = data.get('recaptcha_token', '')

        # Verificar reCAPTCHA si viene token (coherente con otros endpoints)
        if recaptcha_token:
            if not verificar_recaptcha(recaptcha_token):
                return jsonify({ 'success': False, 'message': 'Verificación de seguridad fallida. Intenta nuevamente.' }), 400

        # Validar campos obligatorios (nombre, teléfono y aceptación de política)
        nombre_ok = (datos.get('nombreCliente') or '').strip()
        telefono_ok = (datos.get('telefonoCliente') or '').strip()
        politica_ok = bool(datos.get('aceptaPolitica') or datos.get('acepta_politica'))
        if not (nombre_ok and telefono_ok and politica_ok):
            return jsonify({
                'success': False,
                'message': 'Completa Nombre, Teléfono (WhatsApp) y acepta la Política de Privacidad.'
            }), 400

        # Validar formato de teléfono Colombia (móvil empieza con 3 y tiene 10 dígitos)
        digits = ''.join(ch for ch in telefono_ok if ch.isdigit())
        if digits.startswith('57') and len(digits) == 12:
            digits = digits[2:]
        if not (len(digits) == 10 and digits.startswith('3')):
            return jsonify({
                'success': False,
                'message': 'Teléfono inválido. Usa un móvil de Colombia (inicia en 3 y tiene 10 dígitos).'
            }), 400

        # Determinar receptor del correo (admin)
        admin_email = current_app.config.get('MAIL_DEFAULT_SENDER', 'admin@dh2ocol.com')

        # Construir resumen
        label_map = {
            'limpieza': 'Limpieza de tanque',
            'reparacion': 'Reparación',
            'instalacion': 'Instalación',
            'inspeccion': 'Inspección con dron',
            'otro': 'Otro'
        }
        servicio_label = label_map.get(servicio, 'Servicio')

        def safe_get(k, d=''):
            return (datos.get(k) or d)

        # Construir detalles por servicio (más legible)
        detalles = []
        if servicio in ('limpieza', 'instalacion'):
            if safe_get('tipoTanque'): detalles.append(f"Tipo de tanque: {safe_get('tipoTanque')}")
            if safe_get('capacidadTanque'): detalles.append(f"Capacidad: {safe_get('capacidadTanque')} L")
            if safe_get('accesibilidad'): detalles.append(f"Accesibilidad: {safe_get('accesibilidad')}")
            if servicio == 'instalacion':
                detalles.append(f"Estructura nueva: {safe_get('requiereEstructura', 'no')}")
        elif servicio == 'reparacion':
            if safe_get('tipoDano'): detalles.append(f"Daño reportado: {safe_get('tipoDano')}")
        else:
            if safe_get('descripcionOtro'): detalles.append(f"Descripción: {safe_get('descripcionOtro')}")

        # Formatear moneda y tiempo
        try:
            valor_estimado = int(estimate.get('valor') or 0)
        except Exception:
            valor_estimado = 0
        horas_estimadas = estimate.get('horas') or ''
        valor_cop = f"${valor_estimado:,.0f}".replace(',', '.')

        # Texto plano para compatibilidad
        extra_nota = ''
        try:
            if servicio in ('instalacion', 'reparacion'):
                # Para instalación, condiciona a estructura nueva; reparación no tiene bandera, se menciona en general
                if servicio == 'instalacion' and (datos.get('requiereEstructura') or '').lower() == 'si':
                    extra_nota = ' No incluye accesorios ni materiales cuando se requiere de estructura.'
                else:
                    extra_nota = ' No incluye accesorios ni materiales cuando se requiere de estructura.'
        except Exception:
            pass
        resumen_texto = (
            f"Cotización rápida DH2O\n\n"
            f"Servicio: {servicio_label}\n"
            + ("\n".join(detalles) + "\n\n" if detalles else "") +
            f"Cliente: {safe_get('nombreCliente')} | Tel: {safe_get('telefonoCliente')} | Email: {safe_get('correoCliente')}\n"
            f"Ubicación: {safe_get('barrio')}, {safe_get('ciudad', 'Valledupar')}\nDirección: {safe_get('direccion')}\nReferencia: {safe_get('referencia')}\n"
            f"Mapa: {safe_get('ubicacionMapa')}\n\n"
            f"Estimado: {valor_cop} | Tiempo: {horas_estimadas}\n"
            "Nota: El valor final puede variar tras revisión en sitio." + (extra_nota + "\n" if extra_nota else "\n")
        )

        # Crear mensaje
        msg = Message(
            'Nueva cotización desde wizard - DH2O',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@dh2ocol.com'),
            recipients=[admin_email]
        )
        # Cuerpo HTML profesional (inline CSS para compatibilidad en clientes de correo)
        images_html = ''
        if image_urls:
            thumbs = []
            for u in image_urls:
                thumbs.append(
                    f'<a href="{u}" target="_blank" style="display:inline-block;margin:6px;text-decoration:none;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;background:#fafafa">'
                    f'<img src="{u}" alt="Imagen" style="display:block;width:140px;height:100px;object-fit:cover">'
                    f'</a>'
                )
            images_html = ''.join(thumbs)
        else:
            images_html = '<p style="color:#666;margin:8px 0">Sin imágenes.</p>'

        msg.html = (
            "<div style=\"font-family:Segoe UI,Arial,sans-serif;color:#1f2937;\">"
            "<div style=\"background:linear-gradient(90deg,#2563eb,#0ea5e9);color:#fff;padding:16px 20px;border-radius:10px 10px 0 0;\">"
            "<h2 style=\"margin:0;font-weight:600;\">Nueva cotización | DH2O</h2>"
            f"<div style=\"margin-top:6px;font-size:14px;opacity:.9;\">{servicio_label}</div>"
            "</div>"
            "<div style=\"border:1px solid #e5e7eb;border-top:none;border-radius:0 0 10px 10px;\">"
            "<div style=\"padding:18px 20px;\">"
            "<h3 style=\"margin:0 0 10px;font-size:18px;color:#111827;\">Resumen</h3>"
            f"<p style=\"margin:0 0 12px;color:#374151;\">{ ' • '.join(detalles) if detalles else 'Sin detalles adicionales.' }</p>"
            "<div style=\"display:grid;grid-template-columns:1fr 1fr;gap:12px;\">"
            f"<div><div style=\"font-weight:600;color:#111827;margin-bottom:6px;\">Cliente</div><div style=\"color:#374151;\">{safe_get('nombreCliente')}<br>Tel: {safe_get('telefonoCliente')}<br>Email: {safe_get('correoCliente')}</div></div>"
            f"<div><div style=\"font-weight:600;color:#111827;margin-bottom:6px;\">Ubicación</div><div style=\"color:#374151;\">{safe_get('barrio')}, {safe_get('ciudad','Valledupar')}<br>Dirección: {safe_get('direccion')}<br>Referencia: {safe_get('referencia')}<br>Mapa: <a href=\"{safe_get('ubicacionMapa')}\" target=\"_blank\" style=\"color:#2563eb;text-decoration:none;\">Ver enlace</a></div></div>"
            "</div>"
            "<hr style=\"border:none;border-top:1px solid #e5e7eb;margin:16px 0\">"
            f"<div style=\"display:flex;gap:16px;align-items:center;\"><div style=\"font-weight:600;color:#111827;\">Estimado</div><div style=\"background:#f3f4f6;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;color:#111827;\">{valor_cop}</div><div style=\"font-weight:600;color:#111827;\">Tiempo</div><div style=\"background:#f3f4f6;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;color:#111827;\">{horas_estimadas}</div></div>"
            f"<p style=\"margin-top:10px;color:#6b7280;font-size:12px;\">Nota: El valor final puede variar tras revisión en sitio.{extra_nota}</p>"
            "<h3 style=\"margin:18px 0 8px;font-size:18px;color:#111827;\">Imágenes</h3>"
            f"{images_html}"
            "</div>"
            "</div>"
            "</div>"
        )
        msg.body = resumen_texto

        # Adjuntar imágenes descargándolas desde las URLs (si existen)
        for u in image_urls:
            try:
                r = requests.get(u, timeout=10)
                if r.status_code == 200:
                    # Inferir nombre
                    nombre = u.split('/')[-1].split('?')[0]
                    content_type = r.headers.get('Content-Type', 'image/jpeg')
                    msg.attach(filename=nombre, content_type=content_type, data=r.content)
            except Exception as e:
                print(f"No se pudo adjuntar imagen {u}: {e}")

        # Enviar usando la extensión registrada para evitar importaciones circulares
        mail_ext = current_app.extensions.get('mail')
        if not mail_ext:
            raise RuntimeError('Extensión de mail no inicializada')
        mail_ext.send(msg)
        return jsonify({ 'success': True })
    except Exception as e:
        print(f"Error enviando correo de cotización: {e}")
        return jsonify({ 'success': False, 'message': 'Error al enviar correo' }), 500