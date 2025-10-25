# 🚀 Guía de Deployment con Dockploy - DH2OCOL

## 📋 Resumen

Esta guía detalla el proceso de deployment de la aplicación DH2OCOL usando Dockploy, incluyendo la configuración de variables de entorno, contenedores Docker y base de datos MySQL.

## 🏗️ Arquitectura del Deployment

```
┌─────────────────┐    ┌─────────────────┐
│   Dockploy      │    │     GitHub      │
│   Interface     │◄───┤   Repository    │
└─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Traefik     │    │  Docker Host    │    │     MySQL       │
│ (Reverse Proxy) │◄───┤  (Flask App)    │◄───┤   Container     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuración en Dockploy

### 1. Variables de Entorno Requeridas

Configure las siguientes variables en la interfaz de Dockploy:

#### 🔐 Configuración Básica
```bash
# Flask
FLASK_ENV=production
SECRET_KEY=tu-clave-secreta-super-segura-aqui
FLASK_APP=app.py

# Sitio Web
WEBSITE_URL=https://dh2o.com.co
WEBSITE_NAME=DH2O Colombia
```

#### 🗄️ Base de Datos MySQL
```bash
# Conexión a MySQL
DB_HOST=db
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu-password-mysql-seguro
DB_NAME=flaskdb

# MySQL Container
MYSQL_ROOT_PASSWORD=tu-password-mysql-seguro
MYSQL_DATABASE=flaskdb
```

#### 📧 Configuración de Email (Opcional)
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-password-email
```

#### 🔑 JWT y APIs (Opcional)
```bash
JWT_SECRET_KEY=tu-jwt-secret-key
OPENAI_API_KEY=tu-openai-api-key
```

#### 🐳 Docker
```bash
RUN_MIGRATIONS=true
```

### 2. Configuración del Repositorio

1. **Conectar GitHub**: Vincule su repositorio GitHub con Dockploy
2. **Branch**: Configure `main` o `master` como branch de deployment
3. **Auto-deploy**: Active el auto-deployment en commits

### 3. Configuración de Servicios

#### Servicio Web (Flask)
- **Imagen**: Build desde Dockerfile
- **Puerto**: 5000
- **Health Check**: `/health`
- **Restart Policy**: unless-stopped

#### Servicio Database (MySQL)
- **Imagen**: mysql:8.0
- **Puerto**: 3306
- **Volúmenes**: Persistentes para datos
- **Charset**: utf8mb4

#### Traefik (Proxy Reverso)
- **Configuración**: Automática por Dockploy
- **SSL/TLS**: Let's Encrypt automático
- **Dominio**: Configurado en interfaz
- **Headers**: Automáticos (X-Forwarded-For, etc.)
- **Rate Limiting**: Configurable en Dockploy

## 📁 Estructura de Archivos

```
proyecto/
├── Dockerfile                 # Configuración del contenedor Flask
├── docker-compose.yml         # Orquestación de servicios
├── docker-entrypoint.sh       # Script de inicialización
├── init_db.sql               # Script de inicialización de BD
├── requirements.txt           # Dependencias Python
├── .dockerignore             # Archivos excluidos del build
├── DEPLOYMENT_DOCKPLOY.md     # Documentación de deployment
└── app.py                    # Aplicación principal
```

## 🚀 Proceso de Deployment

### Paso 1: Preparación del Código
```bash
# Verificar que todos los archivos estén en el repositorio
git add .
git commit -m "Preparar para deployment con Dockploy"
git push origin main
```

### Paso 2: Configuración en Dockploy

1. **Crear Nuevo Proyecto**
   - Nombre: `dh2ocol-production`
   - Tipo: Docker Compose

2. **Configurar Variables de Entorno**
   - Agregar todas las variables listadas arriba
   - ⚠️ **IMPORTANTE**: Usar valores seguros en producción

3. **Configurar Dominio y Traefik**
   - Dominio: `dh2o.com.co`
   - SSL: Activar certificado automático (Let's Encrypt)
   - Traefik: Configuración automática de proxy reverso
   - Puerto interno: 5000 (Flask app)

### Paso 3: Deployment

1. **Build Inicial**: Dockploy construirá automáticamente
2. **Verificación**: Comprobar logs de contenedores
3. **Health Check**: Verificar endpoint `/health`

## 🔍 Verificación del Deployment

### Health Check
```bash
curl https://dh2o.com.co/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-XX...",
  "database": "connected",
  "version": "1.0.0"
}
```

### Verificar Servicios
```bash
# En Dockploy, revisar logs de contenedores:
# - dh2ocol-web: Aplicación Flask
# - dh2ocol-db: Base de datos MySQL
```

## 🔧 Comandos Útiles

### Logs de Aplicación
```bash
# Ver logs del contenedor web
docker logs dh2ocol-web -f

# Ver logs de MySQL
docker logs dh2ocol-db -f
```

### Acceso a Contenedores
```bash
# Acceder al contenedor de la aplicación
docker exec -it dh2ocol-web bash

# Acceder a MySQL
docker exec -it dh2ocol-db mysql -u root -p
```

## 🛠️ Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a Base de Datos
```bash
# Verificar variables de entorno
echo $DB_HOST $DB_USER $DB_PASSWORD

# Verificar conectividad
docker exec dh2ocol-web ping db
```

#### 2. Aplicación No Responde
```bash
# Verificar health check
curl http://localhost:5000/health

# Revisar logs
docker logs dh2ocol-web --tail 50
```

#### 3. Variables de Entorno No Cargadas
- Verificar configuración en Dockploy
- Reiniciar contenedores
- Comprobar sintaxis de variables

## 🔄 Actualizaciones

### Deployment Automático
1. Hacer commit al repositorio
2. Push a branch `main`
3. Dockploy detecta cambios automáticamente
4. Rebuild y redeploy automático

### Deployment Manual
1. En Dockploy: ir a proyecto
2. Clic en "Rebuild"
3. Esperar completación
4. Verificar health check

## 📊 Monitoreo

### Métricas Importantes
- **Uptime**: Disponibilidad del servicio
- **Response Time**: Tiempo de respuesta
- **Database Connections**: Conexiones activas
- **Memory Usage**: Uso de memoria
- **CPU Usage**: Uso de CPU

### Alertas Recomendadas
- Health check fallido
- Alto uso de memoria (>80%)
- Alto uso de CPU (>80%)
- Errores de base de datos

## 🔐 Seguridad

### Checklist de Seguridad
- [ ] Variables de entorno seguras
- [ ] SSL/TLS activado
- [ ] Firewall configurado
- [ ] Backups automáticos
- [ ] Logs de seguridad activos
- [ ] Actualizaciones regulares

## 📞 Soporte

### Contactos
- **Administrador**: bdeaguas@dh2o.com.co
- **Documentación**: Este archivo
- **Logs**: Disponibles en Dockploy

### Credenciales de Admin
- **Usuario**: `bdeaguas`
- **Contraseña**: `Mateo2025$`
- **Panel**: `https://dh2o.com.co/admin`

---

## ✅ Estado del Proyecto

- [x] Dockerfile optimizado
- [x] Docker Compose configurado
- [x] Variables de entorno documentadas
- [x] Scripts de inicialización creados
- [x] Health checks implementados
- [x] Documentación completa
- [ ] Deployment en producción
- [ ] Verificación final

**Fecha de última actualización**: $(date)
**Versión**: 1.0.0