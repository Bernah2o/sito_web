// TanquiBot - Chatbot JavaScript
class TanquiBot {
    constructor() {
        this.isOpen = false;
        this.sessionId = this.generateSessionId();
        this.isTyping = false;
        this.recaptchaLoaded = false;
        this.init();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    init() {
        this.createChatbotHTML();
        this.bindEvents();
        this.loadQuickOptions();
        this.showWelcomeMessage();
    }

    createChatbotHTML() {
        const chatbotHTML = `
            <div class="chatbot-container">
                <button class="chatbot-toggle pulse" id="chatbot-toggle" aria-label="Abrir chat" aria-controls="chatbot-window" aria-expanded="false">
                    <i class="fas fa-comments"></i>
                </button>
                
                <div class="chatbot-window" id="chatbot-window" role="dialog" aria-label="Chat de soporte DH2OCOL" aria-modal="false">
                    <div class="chatbot-header">
                        <div>
                            <h4>TanquiBot</h4>
                            <div class="chatbot-status" role="status" aria-live="polite">En línea</div>
                        </div>
                        <button class="chatbot-close" id="chatbot-close" aria-label="Cerrar chat">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="chatbot-messages" id="chatbot-messages" role="log" aria-live="polite" aria-relevant="additions text" aria-atomic="false">
                        <!-- Los mensajes se cargarán aquí -->
                    </div>
                    
                    <div class="quick-options" id="quick-options">
                        <!-- Las opciones rápidas se cargarán aquí -->
                    </div>
                    
                    <div class="chatbot-input-area">
                        <input type="text" class="chatbot-input" id="chatbot-input" 
                               placeholder="Escribe tu pregunta..." maxlength="500" aria-label="Escribe tu pregunta">
                        <button class="chatbot-send" id="chatbot-send" aria-label="Enviar mensaje">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }

    bindEvents() {
        const toggle = document.getElementById('chatbot-toggle');
        const close = document.getElementById('chatbot-close');
        const send = document.getElementById('chatbot-send');
        const input = document.getElementById('chatbot-input');

        toggle.addEventListener('click', () => this.toggleChat());
        close.addEventListener('click', () => this.closeChat());
        send.addEventListener('click', () => this.sendMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        input.addEventListener('input', () => {
            const sendBtn = document.getElementById('chatbot-send');
            sendBtn.disabled = input.value.trim() === '';
        });
    }

    toggleChat() {
        const window = document.getElementById('chatbot-window');
        const toggle = document.getElementById('chatbot-toggle');
        
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        const window = document.getElementById('chatbot-window');
        const toggle = document.getElementById('chatbot-toggle');
        
        window.classList.add('active');
        toggle.classList.remove('pulse');
        toggle.setAttribute('aria-expanded', 'true');
        this.isOpen = true;
        
        // Focus en el input
        setTimeout(() => {
            document.getElementById('chatbot-input').focus();
        }, 300);
    }

    closeChat() {
        const window = document.getElementById('chatbot-window');
        const toggle = document.getElementById('chatbot-toggle');
        
        window.classList.remove('active');
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
        this.isOpen = false;
    }

    showWelcomeMessage() {
        setTimeout(() => {
            this.addBotMessage('¡Hola! 👋 Soy TanquiBot, tu asistente virtual de DH2OCOL. Estoy aquí para ayudarte con información sobre nuestros servicios de tanques de agua. ¿En qué puedo ayudarte hoy?');
        }, 1000);
    }

    async loadQuickOptions() {
        try {
            const response = await fetch('/api/chatbot/opciones-rapidas');
            const options = await response.json();
            
            const container = document.getElementById('quick-options');
            container.innerHTML = '';
            
            options.forEach(option => {
                const button = document.createElement('button');
                button.className = 'quick-option';
                button.textContent = option.pregunta;
                button.setAttribute('aria-label', option.pregunta);
                button.addEventListener('click', () => {
                    this.sendQuickOption(option.pregunta, option.respuesta);
                });
                container.appendChild(button);
            });
        } catch (error) {
            console.error('Error cargando opciones rápidas:', error);
        }
    }

    sendQuickOption(pregunta, respuesta) {
        this.addUserMessage(pregunta);
        setTimeout(() => {
            this.addBotMessage(respuesta);
        }, 800);
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Verificar reCAPTCHA antes de enviar (solo si está configurado correctamente)
        if (typeof grecaptcha !== 'undefined' && window.recaptchaSiteKey && window.recaptchaSiteKey !== '6LfYourSiteKey') {
            try {
                const recaptchaToken = await grecaptcha.execute(window.recaptchaSiteKey, {action: 'chatbot_message'});
                
                // Limpiar input
                input.value = '';
                document.getElementById('chatbot-send').disabled = true;
                
                // Agregar mensaje del usuario
                this.addUserMessage(message);
                
                // Mostrar indicador de escritura
                this.showTypingIndicator();
                
                // Enviar mensaje al servidor con token de reCAPTCHA
                const response = await fetch('/api/chatbot/mensaje', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        mensaje: message,
                        session_id: this.sessionId,
                        recaptcha_token: recaptchaToken
                    })
                });
                
                const data = await response.json();
                
                // Ocultar indicador de escritura
                this.hideTypingIndicator();
                
                if (data.success) {
                    // Agregar respuesta del bot
                    setTimeout(() => {
                        this.addBotMessage(data.respuesta);
                    }, 500);
                } else {
                    this.addBotMessage(data.mensaje || 'Lo siento, ocurrió un error. Por favor, intenta nuevamente o contáctanos directamente.');
                }
                
            } catch (error) {
                console.error('Error con reCAPTCHA:', error);
                this.hideTypingIndicator();
                this.addBotMessage('Error de verificación de seguridad. Por favor, recarga la página e intenta nuevamente.');
            }
        } else {
            // Fallback sin reCAPTCHA
            // Limpiar input
            input.value = '';
            document.getElementById('chatbot-send').disabled = true;
            
            // Agregar mensaje del usuario
            this.addUserMessage(message);
            
            // Mostrar indicador de escritura
            this.showTypingIndicator();
            
            try {
                // Enviar mensaje al servidor
                const response = await fetch('/api/chatbot/mensaje', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        mensaje: message,
                        session_id: this.sessionId
                    })
                });
                
                const data = await response.json();
                
                // Ocultar indicador de escritura
                this.hideTypingIndicator();
                
                if (data.success) {
                    // Agregar respuesta del bot
                    setTimeout(() => {
                        this.addBotMessage(data.respuesta);
                    }, 500);
                } else {
                    this.addBotMessage('Lo siento, ocurrió un error. Por favor, intenta nuevamente o contáctanos directamente.');
                }
                
            } catch (error) {
                console.error('Error enviando mensaje:', error);
                this.hideTypingIndicator();
                this.addBotMessage('Lo siento, no puedo procesar tu mensaje en este momento. Por favor, intenta más tarde.');
            }
        }
        
        // Rehabilitar botón de envío
        setTimeout(() => {
            document.getElementById('chatbot-send').disabled = false;
        }, 1000);
    }

    addUserMessage(message) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageHTML = `
            <div class="chatbot-message user">
                <div class="message-content">${this.escapeHtml(message)}</div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    addBotMessage(message) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageHTML = `
            <div class="chatbot-message bot">
                <div class="bot-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">${this.escapeHtml(message)}</div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        const messagesContainer = document.getElementById('chatbot-messages');
        const typingHTML = `
            <div class="chatbot-message bot" id="typing-indicator">
                <div class="bot-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="typing-indicator">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', typingHTML);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
        this.isTyping = false;
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatbot-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Método para mostrar notificación
    showNotification() {
        const toggle = document.getElementById('chatbot-toggle');
        toggle.classList.add('pulse');
    }
}

// Inicializar el chatbot cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Verificar que Font Awesome esté cargado
    if (typeof FontAwesome !== 'undefined' || document.querySelector('link[href*="font-awesome"]')) {
        new TanquiBot();
    } else {
        // Cargar Font Awesome si no está disponible
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
        document.head.appendChild(link);
        
        link.onload = () => {
            new TanquiBot();
        };
    }
});

// Función global para mostrar notificaciones del chatbot
window.showChatbotNotification = function() {
    const toggle = document.getElementById('chatbot-toggle');
    if (toggle) {
        toggle.classList.add('pulse');
    }
};