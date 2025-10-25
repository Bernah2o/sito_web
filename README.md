# DH2OCOL - Sitio Web Corporativo

## 🌊 Descripción

DH2OCOL es una aplicación web profesional desarrollada en Flask para la empresa especializada en limpieza, desinfección, reparación e instalación de tanques elevados de agua potable. 

La aplicación migra desde WordPress a una solución más administrable y moderna, ofreciendo:

- **Sitio web público** con información de servicios y productos
- **Panel de administración** completo para gestión de contenido
- **Sistema de contactos** con formularios funcionales
- **Base de datos** para contenido dinámico
- **Diseño responsive** y moderno

## 🚀 Características Principales

### Sitio Web Público
- ✅ Página de inicio con servicios destacados
- ✅ Catálogo de servicios dinámico
- ✅ Productos organizados por categorías
- ✅ Formulario de contacto funcional
- ✅ Testimonios de clientes
- ✅ Información corporativa (misión, visión, principios)
- ✅ Descarga de política de tratamiento de datos

### Panel de Administración
- ✅ Dashboard con estadísticas
- ✅ Gestión de servicios (CRUD completo)
- ✅ Gestión de productos por categorías
- ✅ Administración de contactos
- ✅ Gestión de testimonios
- ✅ Configuración del sitio
- ✅ Sistema de autenticación seguro

### Funcionalidades Innovadoras
- 🔄 API para cotización de servicios
- 📱 Diseño completamente responsive
- 🔒 Sistema de sesiones seguro
- 📊 Estadísticas en tiempo real
- 🎨 Interfaz moderna con Bootstrap 5

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Base de Datos**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Autenticación**: Flask Sessions con hash de contraseñas
- **Arquitectura**: Blueprints para organización modular

## 📋 Requisitos Previos

- Python 3.8+
- MySQL 5.7+ o MariaDB 10.3+
- pip (gestor de paquetes de Python)

## ⚡ Instalación Rápida

### 1. Clonar y preparar el entorno

```bash
# Activar entorno virtual
venv\\Scripts\\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Base de Datos

```bash
# Inicializar base de datos
python init_db.py
```

### 3. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

## 🔧 Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y configura:

```env
# Configuración básica
SECRET_KEY=tu-clave-secreta-muy-segura
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=tu-password
DB_NAME=dh2ocol_db
```

### Credenciales por Defecto

- **Usuario Admin**: `admin`
- **Contraseña**: `admin123`
- **Panel Admin**: `http://localhost:5000/admin`

## 📁 Estructura del Proyecto

```
sito_web/
├── app.py                 # Aplicación principal
├── config.py             # Configuración
├── models.py             # Modelos de base de datos
├── init_db.py           # Script de inicialización
├── requirements.txt      # Dependencias
├── blueprints/          # Módulos organizados
│   ├── main.py         # Rutas públicas
│   └── admin.py        # Panel administrativo
├── templates/           # Plantillas HTML
│   ├── sitio/          # Templates públicos
│   └── admin/          # Templates administrativos
├── static/             # Archivos estáticos
│   ├── css/           # Estilos
│   ├── js/            # JavaScript
│   └── img/           # Imágenes
└── venv/              # Entorno virtual
```

## 🎯 Funcionalidades Destacadas

### 1. Sistema de Gestión de Contenido
- Administración completa de servicios y productos
- Editor de contenido dinámico
- Gestión de imágenes y archivos

#### 📸 Gestión de Carrusel de Imágenes
- **Categoría**: Asignar imágenes a la categoría "Carrusel" en el panel de administración
- **Tamaño recomendado**: 1920x1080 píxeles (16:9)
- **Tamaño mínimo**: 1200x675 píxeles
- **Formato**: JPG, PNG, GIF
- **Peso máximo**: 5MB por imagen
- **Descripción**: Incluir texto descriptivo para las leyendas del carrusel
- **Visualización**: Las imágenes se muestran automáticamente en la página de inicio
- **Fallback**: Si no hay imágenes en la categoría "Carrusel", se muestran imágenes por defecto

### 2. Sistema de Contactos
- Formulario con validación
- Almacenamiento en base de datos
- Estados de seguimiento (nuevo, en proceso, completado)

### 3. Panel de Estadísticas
- Métricas en tiempo real
- Últimos contactos
- Acciones rápidas

### 4. API de Cotización
```javascript
// Ejemplo de uso de la API
fetch('/api/cotizar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        tipo_servicio: 'limpieza',
        cantidad_tanques: 3
    })
})
```

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con Werkzeug
- ✅ Sesiones seguras con Flask
- ✅ Validación de formularios
- ✅ Protección CSRF
- ✅ Sanitización de datos

## 🚀 Despliegue en Producción

### 1. Configurar para Producción

```python
# En config.py
FLASK_ENV=production
DEBUG=False
```

### 2. Servidor Web

Recomendado: Gunicorn + Nginx

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📈 Próximas Mejoras

- [ ] Sistema de citas online
- [ ] Calculadora avanzada de servicios
- [ ] Integración con WhatsApp Business
- [ ] Sistema de notificaciones por email
- [ ] Dashboard de analytics avanzado
- [ ] API REST completa
- [ ] App móvil complementaria

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico o consultas:

- **Email**: contacto@dh2ocol.com
- **Teléfono**: +57 315 748 4662
- **Sitio Web**: https://dh2o.com.co

## 📄 Licencia

Este proyecto es propiedad de DH2OCOL. Todos los derechos reservados.

---

**DH2OCOL** - *Cuidando cada gota para un futuro más saludable* 🌊