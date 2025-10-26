from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class DatabaseManager:
    """Gestor de base de datos para DH2OCOL"""
    
    def __init__(self, mysql):
        self.mysql = mysql
    
    def init_db(self):
        """Inicializa las tablas de la base de datos"""
        cursor = self.mysql.connection.cursor()
        
        # Tabla de servicios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servicios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                descripcion TEXT,
                imagen VARCHAR(1000),
                precio DECIMAL(10,2),
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                descripcion TEXT,
                imagen VARCHAR(1000),
                precio DECIMAL(10,2),
                categoria VARCHAR(100),
                stock INT DEFAULT 0,
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de testimonios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS testimonios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre_cliente VARCHAR(255) NOT NULL,
                empresa VARCHAR(255),
                testimonio TEXT NOT NULL,
                calificacion INT DEFAULT 5,
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de contactos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contactos (
                id INT AUTO_INCREMENT PRIMARY KEY,
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
        
        # Tabla de usuarios admin
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                nombre VARCHAR(255),
                activo BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de configuración del sitio
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracion (
                id INT AUTO_INCREMENT PRIMARY KEY,
                clave VARCHAR(255) UNIQUE NOT NULL,
                valor TEXT,
                descripcion TEXT,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de preguntas del chatbot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_preguntas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pregunta TEXT NOT NULL,
                respuesta TEXT NOT NULL,
                palabras_clave TEXT,
                categoria VARCHAR(100),
                activo BOOLEAN DEFAULT TRUE,
                orden INT DEFAULT 0,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de conversaciones del chatbot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_conversaciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                pregunta_usuario TEXT NOT NULL,
                respuesta_bot TEXT NOT NULL,
                pregunta_id INT,
                ip_usuario VARCHAR(45),
                user_agent TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pregunta_id) REFERENCES chatbot_preguntas(id)
            )
        ''')
        
        # Tabla de configuración del chatbot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chatbot_configuracion (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre_bot VARCHAR(100) DEFAULT 'TanquiBot',
                mensaje_bienvenida TEXT DEFAULT '¡Hola! Soy TanquiBot, tu asistente virtual. ¿En qué puedo ayudarte hoy?',
                mensaje_no_entendido TEXT DEFAULT 'Lo siento, no entiendo tu pregunta. ¿Podrías reformularla o elegir una de las opciones disponibles?',
                activo BOOLEAN DEFAULT TRUE,
                recaptcha_site_key VARCHAR(255),
                recaptcha_secret_key VARCHAR(255),
                openai_api_key VARCHAR(255),
                usar_gpt BOOLEAN DEFAULT FALSE,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        self.mysql.connection.commit()
        cursor.close()
    
    def insertar_datos_iniciales(self):
        """Inserta datos iniciales en la base de datos"""
        cursor = self.mysql.connection.cursor()
        
        # Servicios iniciales
        servicios_iniciales = [
            ('Limpieza y Desinfección', 'Realizamos limpieza y desinfección de tanques elevados, eliminando bacterias y microorganismos para garantizar agua segura, limpia y de alta calidad para tu hogar o negocio.', 'desinfeccion.jpg', 150000),
            ('Reparación', 'Brindamos servicios especializados en la reparación de tanques elevados de agua potable, enfocados en resolver problemas técnicos y desgaste.', 'reparacion.jpg', 200000),
            ('Instalación', 'Servicio técnico y mantenimiento preventivo y correctivo para sus sistemas de tratamiento.', 'instalacion.jpg', 300000)
        ]
        
        for servicio in servicios_iniciales:
            cursor.execute('''
                INSERT IGNORE INTO servicios (titulo, descripcion, imagen, precio)
                VALUES (%s, %s, %s, %s)
            ''', servicio)
        
        # Productos iniciales
        productos_iniciales = [
            ('Válvula Flotadora', 'Conjunto válvula tanque 1/2 pulg con flotador: controla nivel de agua automático.', 'valvula_flotadora.jpg', 45000, 'Accesorios', 50),
            ('Flanche Adaptador', 'Adaptador PP blanco para salida de tanque de agua.', 'flanche_adaptador.jpg', 25000, 'Accesorios', 30),
            ('Unión Universal', 'Facilita instalación y reparación.', 'union_universal.jpg', 35000, 'Accesorios', 40)
        ]
        
        for producto in productos_iniciales:
            cursor.execute('''
                INSERT IGNORE INTO productos (nombre, descripcion, imagen, precio, categoria, stock)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', producto)
        
        # Testimonios iniciales
        testimonios_iniciales = [
            ('María González', 'Edificio Residencial Los Pinos', 'Excelente servicio profesional. Cuentan con personal altamente calificado, las herramientas adecuadas para una limpieza eficiente de los tanques y brindan una atención al cliente excepcional. ¡Totalmente recomendado!', 5),
            ('Carlos Rodríguez', 'Conjunto Residencial El Parque', 'Excelente servicio recomendados al 100% matriculados con ustedes.', 5),
            ('Ana Martínez', 'Empresa Servicios Integrales', 'Excelente servicio, son muy cuidados con los productos que usan para ayudar al medio ambiente. Se los recomiendo a todos.', 5)
        ]
        
        for testimonio in testimonios_iniciales:
            cursor.execute('''
                INSERT IGNORE INTO testimonios (nombre_cliente, empresa, testimonio, calificacion)
                VALUES (%s, %s, %s, %s)
            ''', testimonio)
        
        # Configuración inicial
        configuracion_inicial = [
            ('empresa_nombre', 'DH2OCOL', 'Nombre de la empresa'),
            ('empresa_slogan', 'Cuidando cada gota para un futuro más saludable', 'Slogan de la empresa'),
            ('empresa_telefono', '+57 3157484662', 'Teléfono principal'),
            ('empresa_email', 'contacto@dh2o.com.co', 'Email de contacto'),
            ('empresa_direccion', 'Valledupar, Colombia', 'Dirección de la empresa'),
            ('whatsapp_numero', '+57 3157484662', 'Número de WhatsApp'),
            ('facebook_url', 'https://facebook.com/dh2ocol', 'URL de Facebook'),
            ('instagram_url', 'https://instagram.com/dh2ocol', 'URL de Instagram'),
            ('youtube_url', 'https://youtube.com/dh2ocol', 'URL de YouTube')
        ]
        
        for config in configuracion_inicial:
            cursor.execute('''
                INSERT IGNORE INTO configuracion (clave, valor, descripcion)
                VALUES (%s, %s, %s)
            ''', config)
        
        # Preguntas iniciales del chatbot
        preguntas_chatbot = [
            ('¿Qué servicios ofrecen?', 'Ofrecemos servicios de limpieza y desinfección, reparación e instalación de tanques elevados de agua potable. Nuestro objetivo es garantizar agua segura y de alta calidad.', 'servicios, que hacen, ofrecen', 'Servicios', 1),
            ('¿Cuánto cuesta la limpieza de tanques?', 'El costo de limpieza y desinfección es de $150.000. Este servicio incluye eliminación de bacterias y microorganismos para garantizar agua segura.', 'precio, costo, limpieza, cuanto', 'Precios', 2),
            ('¿Hacen reparaciones?', 'Sí, brindamos servicios especializados en reparación de tanques elevados. El costo es de $200.000 y nos enfocamos en resolver problemas técnicos y desgaste.', 'reparacion, arreglo, daño', 'Servicios', 3),
            ('¿Dónde están ubicados?', 'Estamos ubicados en Valledupar, Colombia. Puedes contactarnos al +57 3157484662 o escribirnos a contacto@dh2o.com.co', 'ubicacion, donde, direccion, contacto', 'Contacto', 4),
            ('¿Cómo puedo contactarlos?', 'Puedes contactarnos por WhatsApp al +57 3157484662, por email a contacto@dh2o.com.co, o a través de nuestras redes sociales.', 'contacto, telefono, whatsapp, email', 'Contacto', 5),
            ('¿Venden accesorios para tanques?', 'Sí, vendemos diversos accesorios como válvulas flotadoras ($45.000), flanches adaptadores ($25.000) y uniones universales ($35.000).', 'accesorios, productos, valvula, flanche', 'Productos', 6),
            ('¿Con qué frecuencia debo limpiar mi tanque?', 'Recomendamos limpiar y desinfectar los tanques cada 6 meses para mantener la calidad del agua y prevenir la acumulación de bacterias.', 'frecuencia, cada cuanto, mantenimiento', 'Mantenimiento', 7),
            ('¿Qué incluye el servicio de instalación?', 'El servicio de instalación ($300.000) incluye servicio técnico y mantenimiento preventivo y correctivo para sistemas de tratamiento de agua.', 'instalacion, que incluye, servicio tecnico', 'Servicios', 8)
        ]
        
        for pregunta in preguntas_chatbot:
            cursor.execute('''
                INSERT IGNORE INTO chatbot_preguntas (pregunta, respuesta, palabras_clave, categoria, orden)
                VALUES (%s, %s, %s, %s, %s)
            ''', pregunta)
        
        # Configuración inicial del chatbot
        cursor.execute('''
            INSERT IGNORE INTO chatbot_configuracion (id, nombre_bot, mensaje_bienvenida, mensaje_no_entendido, activo)
            VALUES (1, 'TanquiBot', '¡Hola! 👋 Soy TanquiBot, tu asistente virtual de DH2OCOL. Estoy aquí para ayudarte con información sobre nuestros servicios de tanques de agua. ¿En qué puedo ayudarte hoy?', 'Lo siento, no entiendo tu pregunta. 🤔 ¿Podrías reformularla o elegir una de las opciones disponibles? También puedes contactarnos directamente por WhatsApp.', TRUE)
        ''')
        
        self.mysql.connection.commit()
        cursor.close()

class Usuario:
    """Clase para manejar usuarios del sistema"""
    
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash
    
    @staticmethod
    def verificar_password(password_hash, password):
        """Verificar contraseña"""
        from werkzeug.security import check_password_hash
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def hash_password(password):
        """Generar hash de contraseña"""
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password)



def get_mysql_init_sql():
    """Retorna comandos SQL para inicializar MySQL"""
    from werkzeug.security import generate_password_hash
    
    commands = [
        # Tabla de servicios
        """CREATE TABLE IF NOT EXISTS servicios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            precio_base DECIMAL(10,2),
            imagen VARCHAR(1000),
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        
        # Tabla de productos
        """CREATE TABLE IF NOT EXISTS productos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT,
            precio DECIMAL(10,2),
            categoria VARCHAR(50),
            imagen VARCHAR(1000),
            stock INT DEFAULT 0,
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        
        # Tabla de testimonios
        """CREATE TABLE IF NOT EXISTS testimonios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre_cliente VARCHAR(100) NOT NULL,
            empresa VARCHAR(100),
            testimonio TEXT NOT NULL,
            calificacion INT CHECK(calificacion >= 1 AND calificacion <= 5),
            imagen VARCHAR(1000),
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        
        # Tabla de contactos
        """CREATE TABLE IF NOT EXISTS contactos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            telefono VARCHAR(20),
            empresa VARCHAR(100),
            mensaje TEXT NOT NULL,
            estado ENUM('nuevo', 'en_proceso', 'completado') DEFAULT 'nuevo',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        
        # Tabla de usuarios admin
        """CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        
        # Tabla de medios
        """CREATE TABLE IF NOT EXISTS medios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            categoria VARCHAR(50) DEFAULT 'general',
            tamano INT,
            descripcion TEXT,
            ruta VARCHAR(1000) NOT NULL,
            fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        
        # Tabla de configuración del sitio
        """CREATE TABLE IF NOT EXISTS configuracion (
            id INT AUTO_INCREMENT PRIMARY KEY,
            clave VARCHAR(50) UNIQUE NOT NULL,
            valor TEXT,
            descripcion VARCHAR(255),
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        
        # Tabla de tokens de restablecimiento de contraseña
        """CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            token VARCHAR(255) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        
        # Insertar servicios iniciales
        """INSERT IGNORE INTO servicios (nombre, descripcion, precio_base, activo) VALUES
        ('Limpieza de Tanques', 'Limpieza profunda y desinfección de tanques de agua potable', 150000.00, TRUE),
        ('Reparación de Tanques', 'Reparación de grietas, fugas y daños estructurales', 200000.00, TRUE),
        ('Instalación de Tanques', 'Instalación completa de tanques elevados nuevos', 500000.00, TRUE),
        ('Mantenimiento Preventivo', 'Programa de mantenimiento regular para tanques', 100000.00, TRUE)""",
        
        # Insertar productos iniciales
        """INSERT IGNORE INTO productos (nombre, descripcion, precio, categoria, stock, activo) VALUES
        ('Tanque 500L', 'Tanque de polietileno de 500 litros', 250000.00, 'tanques', 10, TRUE),
        ('Tanque 1000L', 'Tanque de polietileno de 1000 litros', 450000.00, 'tanques', 8, TRUE),
        ('Kit de Limpieza', 'Kit completo para limpieza de tanques', 75000.00, 'accesorios', 25, TRUE),
        ('Válvula de Entrada', 'Válvula de entrada para tanques', 35000.00, 'accesorios', 50, TRUE)""",
        
        # Insertar testimonios iniciales
        """INSERT IGNORE INTO testimonios (nombre_cliente, empresa, testimonio, calificacion, activo) VALUES
        ('María González', 'Edificio Los Pinos', 'Excelente servicio, muy profesionales y puntuales', 5, TRUE),
        ('Carlos Rodríguez', 'Conjunto Residencial El Parque', 'Quedamos muy satisfechos con la limpieza del tanque', 5, TRUE),
        ('Ana Martínez', 'Hotel Plaza', 'Servicio de calidad, recomendados 100%', 4, TRUE)""",
        
        # Insertar usuario admin por defecto
        f"""INSERT IGNORE INTO usuarios (username, password_hash, email, activo) VALUES
        ('admin', '{generate_password_hash("admin123")}', 'admin@dh2ocol.com', TRUE)""",
        
        # Insertar configuración inicial
        """INSERT IGNORE INTO configuracion (clave, valor, descripcion) VALUES
        ('nombre_empresa', 'DH2OCOL', 'Nombre de la empresa'),
        ('telefono', '+57 315 748 4662', 'Teléfono principal'),
        ('email', 'contacto@dh2ocol.com', 'Email de contacto'),
        ('direccion', 'Valledupar', 'Dirección principal'),
        ('mision', 'Brindar servicios especializados en limpieza y mantenimiento de tanques de agua potable', 'Misión de la empresa'),
        ('vision', 'Ser la empresa líder en servicios de tanques de agua en Colombia', 'Visión de la empresa')""",
    ]
    
    return commands