"""
Utilidades para envío de emails
"""

from flask import current_app
from flask_mail import Message
from app import mail
import logging

def send_password_reset_email(user_email, reset_token, username):
    """
    Enviar email de restablecimiento de contraseña
    
    Args:
        user_email (str): Email del usuario
        reset_token (str): Token de restablecimiento
        username (str): Nombre de usuario
    
    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    try:
        from flask import url_for
        
        # Generar URL de restablecimiento
        reset_url = url_for('admin.reset_password', token=reset_token, _external=True)
        
        # Crear mensaje
        msg = Message(
            'Restablecimiento de Contraseña - DH2OCOL',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@dh2ocol.com'),
            recipients=[user_email]
        )
        
        # Contenido HTML del email
        msg.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Restablecimiento de Contraseña</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">DH2OCOL</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Servicios Especializados en Tanques de Agua</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border: 1px solid #e0e0e0; border-top: none;">
                <h2 style="color: #333; margin-top: 0; font-size: 24px;">Restablecimiento de Contraseña</h2>
                
                <p style="font-size: 16px; margin-bottom: 20px;">Hola <strong>{username}</strong>,</p>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en el panel administrativo de DH2OCOL.
                </p>
                
                <p style="font-size: 16px; margin-bottom: 30px;">
                    Para crear una nueva contraseña, haz clic en el siguiente botón:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 30px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold; 
                              font-size: 16px; 
                              display: inline-block;">
                        Restablecer Contraseña
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Si no puedes hacer clic en el botón, copia y pega el siguiente enlace en tu navegador:
                </p>
                <p style="font-size: 14px; color: #007bff; word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 5px;">
                    {reset_url}
                </p>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #856404;">
                        <strong>⚠️ Importante:</strong> Este enlace es válido por 1 hora. Si no solicitaste este restablecimiento, puedes ignorar este email.
                    </p>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Si tienes alguna pregunta o necesitas ayuda, no dudes en contactarnos.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    Saludos,<br>
                    <strong>Equipo DH2OCOL</strong>
                </p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0; border-top: none;">
                <p style="margin: 0; font-size: 12px; color: #666;">
                    © 2024 DH2OCOL - Servicios Especializados en Tanques de Agua
                </p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">
                    Valledupar, Colombia | +57 315 748 4662
                </p>
            </div>
        </body>
        </html>
        """
        
        # Contenido de texto plano como respaldo
        msg.body = f"""
        Restablecimiento de Contraseña - DH2OCOL
        
        Hola {username},
        
        Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.
        
        Para crear una nueva contraseña, visita el siguiente enlace:
        {reset_url}
        
        Este enlace es válido por 1 hora.
        
        Si no solicitaste este restablecimiento, puedes ignorar este email.
        
        Saludos,
        Equipo DH2OCOL
        """
        
        # Enviar email
        mail.send(msg)
        return True
        
    except Exception as e:
        logging.error(f"Error al enviar email de restablecimiento: {e}")
        return False

def send_contact_email(nombre, email, telefono, empresa, mensaje):
    """
    Enviar email de notificación de contacto
    
    Args:
        nombre (str): Nombre del contacto
        email (str): Email del contacto
        telefono (str): Teléfono del contacto (opcional)
        empresa (str): Empresa del contacto (opcional)
        mensaje (str): Mensaje del contacto
    
    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    try:
        # Email de notificación para el administrador
        admin_email = current_app.config.get('MAIL_DEFAULT_SENDER', 'admin@dh2ocol.com')
        
        # Crear mensaje para el administrador
        msg_admin = Message(
            f'Nuevo Contacto desde el Sitio Web - {nombre}',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@dh2ocol.com'),
            recipients=[admin_email]
        )
        
        # Contenido HTML del email para el administrador
        msg_admin.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Nuevo Contacto - DH2OCOL</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">DH2OCOL</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Nuevo Contacto desde el Sitio Web</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border: 1px solid #e0e0e0; border-top: none;">
                <h2 style="color: #333; margin-top: 0; font-size: 24px;">Información del Contacto</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0 0 10px 0; font-size: 16px;"><strong>Nombre:</strong> {nombre}</p>
                    <p style="margin: 0 0 10px 0; font-size: 16px;"><strong>Email:</strong> {email}</p>
                    {f'<p style="margin: 0 0 10px 0; font-size: 16px;"><strong>Teléfono:</strong> {telefono}</p>' if telefono else ''}
                    {f'<p style="margin: 0 0 10px 0; font-size: 16px;"><strong>Empresa:</strong> {empresa}</p>' if empresa else ''}
                </div>
                
                <h3 style="color: #333; font-size: 18px;">Mensaje:</h3>
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0;">
                    <p style="margin: 0; font-size: 16px; white-space: pre-wrap;">{mensaje}</p>
                </div>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #155724;">
                        <strong>📧 Acción requerida:</strong> Responde a este contacto lo antes posible para brindar un excelente servicio al cliente.
                    </p>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0; border-top: none;">
                <p style="margin: 0; font-size: 12px; color: #666;">
                    © 2024 DH2OCOL - Sistema de Notificaciones
                </p>
            </div>
        </body>
        </html>
        """
        
        # Contenido de texto plano como respaldo
        msg_admin.body = f"""
        Nuevo Contacto desde el Sitio Web - DH2OCOL
        
        Información del Contacto:
        - Nombre: {nombre}
        - Email: {email}
        {f'- Teléfono: {telefono}' if telefono else ''}
        {f'- Empresa: {empresa}' if empresa else ''}
        
        Mensaje:
        {mensaje}
        
        Responde a este contacto lo antes posible.
        """
        
        # Enviar email al administrador
        mail.send(msg_admin)
        
        # Email de confirmación para el cliente
        msg_cliente = Message(
            'Confirmación de Contacto - DH2OCOL',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@dh2ocol.com'),
            recipients=[email]
        )
        
        # Contenido HTML del email para el cliente
        msg_cliente.html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Confirmación de Contacto - DH2OCOL</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">DH2OCOL</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Servicios Especializados en Tanques de Agua</p>
            </div>
            
            <div style="background: #ffffff; padding: 40px; border: 1px solid #e0e0e0; border-top: none;">
                <h2 style="color: #333; margin-top: 0; font-size: 24px;">¡Gracias por contactarnos!</h2>
                
                <p style="font-size: 16px; margin-bottom: 20px;">Hola <strong>{nombre}</strong>,</p>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Hemos recibido tu mensaje y queremos agradecerte por contactar a DH2OCOL. 
                    Nuestro equipo revisará tu consulta y te responderemos lo antes posible.
                </p>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 14px; color: #155724;">
                        <strong>✅ Tu mensaje ha sido recibido:</strong> Normalmente respondemos en un plazo de 24 horas durante días hábiles.
                    </p>
                </div>
                
                <h3 style="color: #333; font-size: 18px;">Resumen de tu consulta:</h3>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p style="margin: 0; font-size: 14px; white-space: pre-wrap;">{mensaje}</p>
                </div>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Mientras tanto, puedes seguirnos en nuestras redes sociales para conocer más sobre nuestros servicios:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://wa.me/573157484662" style="background: #25d366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 0 5px; display: inline-block;">WhatsApp</a>
                    <a href="https://facebook.com/dh2ocol" style="background: #1877f2; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 0 5px; display: inline-block;">Facebook</a>
                    <a href="https://instagram.com/dh2ocol" style="background: #e4405f; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 0 5px; display: inline-block;">Instagram</a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Si tienes alguna pregunta urgente, no dudes en contactarnos directamente al +57 315 748 4662.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    Saludos,<br>
                    <strong>Equipo DH2OCOL</strong>
                </p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #e0e0e0; border-top: none;">
                <p style="margin: 0; font-size: 12px; color: #666;">
                    © 2024 DH2OCOL - Servicios Especializados en Tanques de Agua
                </p>
                <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">
                    Valledupar, Colombia | +57 315 748 4662
                </p>
            </div>
        </body>
        </html>
        """
        
        # Contenido de texto plano como respaldo
        msg_cliente.body = f"""
        Confirmación de Contacto - DH2OCOL
        
        Hola {nombre},
        
        Hemos recibido tu mensaje y queremos agradecerte por contactar a DH2OCOL.
        Nuestro equipo revisará tu consulta y te responderemos lo antes posible.
        
        Resumen de tu consulta:
        {mensaje}
        
        Normalmente respondemos en un plazo de 24 horas durante días hábiles.
        
        Si tienes alguna pregunta urgente, contactanos al +57 315 748 4662.
        
        Saludos,
        Equipo DH2OCOL
        """
        
        # Enviar email de confirmación al cliente
        mail.send(msg_cliente)
        
        return True
        
    except Exception as e:
        logging.error(f"Error al enviar email de contacto: {e}")
        return False

def test_email_configuration():
    """
    Probar la configuración de email
    
    Returns:
        dict: Resultado de la prueba
    """
    try:
        # Verificar configuración
        config_ok = all([
            current_app.config.get('MAIL_SERVER'),
            current_app.config.get('MAIL_USERNAME'),
            current_app.config.get('MAIL_PASSWORD')
        ])
        
        if not config_ok:
            return {
                'success': False,
                'message': 'Configuración de email incompleta. Verifica MAIL_SERVER, MAIL_USERNAME y MAIL_PASSWORD en las variables de entorno.'
            }
        
        return {
            'success': True,
            'message': 'Configuración de email correcta',
            'config': {
                'server': current_app.config.get('MAIL_SERVER'),
                'port': current_app.config.get('MAIL_PORT'),
                'username': current_app.config.get('MAIL_USERNAME'),
                'use_tls': current_app.config.get('MAIL_USE_TLS'),
                'default_sender': current_app.config.get('MAIL_DEFAULT_SENDER')
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error al verificar configuración: {e}'
        }