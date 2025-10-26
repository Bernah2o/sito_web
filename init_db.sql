-- Script de inicialización para MySQL en Docker
-- Este script se ejecuta automáticamente cuando se crea el contenedor

-- Configurar charset y collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS flaskdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE flaskdb;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de servicios
CREATE TABLE IF NOT EXISTS servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2),
    imagen VARCHAR(255),
    categoria VARCHAR(100),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de testimonios
CREATE TABLE IF NOT EXISTS testimonios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_cliente VARCHAR(100) NOT NULL,
    empresa VARCHAR(100),
    testimonio TEXT NOT NULL,
    calificacion INT DEFAULT 5,
    imagen VARCHAR(1000),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de contactos
CREATE TABLE IF NOT EXISTS contactos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    telefono VARCHAR(20),
    mensaje TEXT NOT NULL,
    leido BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de tokens de reset de contraseña
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    token VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE
);

-- Insertar usuario administrador por defecto
INSERT IGNORE INTO usuarios (username, password, email, role) 
VALUES ('bdeaguas', SHA2('Mateo2025$', 256), 'bdeaguas@dh2o.com.co', 'admin');

-- Insertar servicios por defecto
INSERT IGNORE INTO servicios (nombre, descripcion, precio, categoria) VALUES
('Limpieza y Desinfección de Tanques', 'Servicio completo de limpieza y desinfección de tanques elevados con productos biodegradables', 150000.00, 'limpieza'),
('Reparación de Tanques', 'Reparación especializada de tanques elevados, sellado de fisuras y cambio de accesorios', 200000.00, 'reparacion'),
('Instalación de Tanques', 'Instalación profesional de tanques elevados con garantía y mantenimiento', 500000.00, 'instalacion'),
('Mantenimiento Preventivo', 'Programa de mantenimiento preventivo para garantizar la calidad del agua', 100000.00, 'mantenimiento');

-- Insertar testimonios por defecto
INSERT IGNORE INTO testimonios (nombre_cliente, empresa, testimonio, calificacion) VALUES
('María González', 'Edificio Los Pinos', 'Excelente servicio profesional. Cuentan con personal altamente calificado, las herramientas adecuadas para una limpieza eficiente de los tanques y brindan una atención al cliente excepcional. ¡Totalmente recomendado!', 5),
('Carlos Rodríguez', 'Conjunto Residencial El Parque', 'Excelente servicio recomendados al 100% matriculados con ustedes.', 5),
('Ana Martínez', 'Hotel Plaza', 'Excelente servicio, son muy cuidados con los productos que usan para ayudar al medio ambiente. Se los recomiendo a todos.', 5);

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_servicios_categoria ON servicios(categoria);
CREATE INDEX IF NOT EXISTS idx_servicios_activo ON servicios(activo);
CREATE INDEX IF NOT EXISTS idx_testimonios_activo ON testimonios(activo);
CREATE INDEX IF NOT EXISTS idx_contactos_leido ON contactos(leido);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_email ON password_reset_tokens(email);