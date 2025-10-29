/**
 * Contador de Visitantes para DH2OCOL
 * Múltiples implementaciones disponibles
 */

class VisitorCounter {
    constructor(options = {}) {
        this.options = {
            storageKey: 'dh2ocol_visitor_count',
            sessionKey: 'dh2ocol_session_visit',
            displayElementId: 'visitor-counter',
            apiEndpoint: '/api/visitor-count',
            enableAnalytics: false,
            ...options
        };
        
        this.init();
    }

    /**
     * Inicializar el contador
     */
    init() {
        // Verificar si es una nueva sesión
        if (!this.isSessionVisit()) {
            this.incrementCounter();
            this.markSessionVisit();
        }
        
        this.displayCounter();
        
        // Si analytics está habilitado, enviar datos al servidor
        if (this.options.enableAnalytics) {
            this.sendAnalytics();
        }
    }

    /**
     * 1. CONTADOR BÁSICO CON LOCALSTORAGE
     * Incrementa el contador local del navegador
     */
    incrementCounter() {
        let count = this.getLocalCount();
        count++;
        localStorage.setItem(this.options.storageKey, count.toString());
        console.log(`Visitante #${count} registrado`);
        return count;
    }

    /**
     * Obtener contador local
     */
    getLocalCount() {
        const count = localStorage.getItem(this.options.storageKey);
        return count ? parseInt(count) : 0;
    }

    /**
     * 2. CONTADOR ÚNICO POR SESIÓN
     * Evita contar múltiples visitas en la misma sesión
     */
    isSessionVisit() {
        return sessionStorage.getItem(this.options.sessionKey) !== null;
    }

    markSessionVisit() {
        sessionStorage.setItem(this.options.sessionKey, Date.now().toString());
    }

    /**
     * 3. CONTADOR PERSISTENTE CON BACKEND
     * Envía datos al servidor para persistencia
     */
    async sendToServer() {
        try {
            const response = await fetch(this.options.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    timestamp: Date.now(),
                    userAgent: navigator.userAgent,
                    referrer: document.referrer,
                    page: window.location.pathname
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Visita registrada en servidor:', data);
                return data;
            }
        } catch (error) {
            console.error('Error enviando datos al servidor:', error);
        }
    }

    /**
     * Registrar visita con datos adicionales
     */
    async registerVisit(additionalData = {}) {
        try {
            const visitData = {
                timestamp: Date.now(),
                sessionId: this.getSessionId(),
                userAgent: navigator.userAgent,
                referrer: document.referrer,
                page: window.location.pathname,
                screenResolution: `${screen.width}x${screen.height}`,
                language: navigator.language,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                ...additionalData
            };

            if (this.options.useBackend) {
                const response = await fetch(this.options.apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(visitData)
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log('Visita registrada:', data);
                    this.updateDisplayFromServer(data);
                    return data;
                }
            } else {
                // Fallback a contador local
                this.incrementCounter();
            }
        } catch (error) {
            console.error('Error registrando visita:', error);
            // Fallback a contador local en caso de error
            this.incrementCounter();
        }
    }

    /**
     * Actualizar display desde datos del servidor
     */
    updateDisplayFromServer(data) {
        if (data.total_visitors) {
            const countElement = document.getElementById('visitor-count');
            if (countElement) {
                countElement.textContent = data.total_visitors;
            }
        }
    }

    /**
     * Actualizar estadísticas desde el servidor
     */
    async updateStats() {
        if (!this.options.statsEndpoint) return;

        try {
            const response = await fetch(this.options.statsEndpoint);
            if (response.ok) {
                const stats = await response.json();
                this.displayStats(stats);
            }
        } catch (error) {
            console.error('Error obteniendo estadísticas:', error);
        }
    }

    /**
     * 4. ANALYTICS AVANZADOS
     * Recopila información detallada del visitante
     */
    async sendAnalytics() {
        const analyticsData = {
            timestamp: Date.now(),
            page: window.location.pathname,
            referrer: document.referrer,
            userAgent: navigator.userAgent,
            screenResolution: `${screen.width}x${screen.height}`,
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            isNewVisitor: this.getLocalCount() === 1,
            sessionId: this.getSessionId(),
            localCount: this.getLocalCount()
        };

        try {
            const response = await fetch('/api/analytics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(analyticsData)
            });

            if (response.ok) {
                console.log('Analytics enviados correctamente');
            }
        } catch (error) {
            console.error('Error enviando analytics:', error);
        }
    }

    /**
     * Generar ID de sesión único
     */
    getSessionId() {
        let sessionId = sessionStorage.getItem('dh2ocol_session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('dh2ocol_session_id', sessionId);
        }
        return sessionId;
    }

    /**
     * 5. VISUALIZACIÓN DEL CONTADOR
     * Muestra el contador en la página
     */
    displayCounter() {
        const element = document.getElementById(this.options.displayElementId);
        if (element) {
            const count = this.getLocalCount();
            element.innerHTML = this.formatCounterDisplay(count);
        }
    }

    formatCounterDisplay(count) {
        return `
            <div class="visitor-counter">
                <i class="fas fa-users"></i>
                <span class="counter-number">${count.toLocaleString()}</span>
                <span class="counter-label">visitantes</span>
            </div>
        `;
    }

    /**
     * 6. CONTADOR CON ANIMACIÓN
     * Anima el número del contador
     */
    animateCounter(targetCount, duration = 2000) {
        const element = document.getElementById(this.options.displayElementId);
        if (!element) return;

        let startCount = 0;
        const increment = targetCount / (duration / 16); // 60 FPS
        
        const animate = () => {
            startCount += increment;
            if (startCount < targetCount) {
                element.textContent = Math.floor(startCount).toLocaleString();
                requestAnimationFrame(animate);
            } else {
                element.textContent = targetCount.toLocaleString();
            }
        };
        
        animate();
    }

    /**
     * 7. CONTADOR CON GEOLOCALIZACIÓN
     * Incluye información de ubicación (con permiso del usuario)
     */
    async getLocationData() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve(null);
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                },
                () => resolve(null),
                { timeout: 5000, enableHighAccuracy: false }
            );
        });
    }

    /**
     * 8. ESTADÍSTICAS EN TIEMPO REAL
     * Obtiene estadísticas del servidor
     */
    async getServerStats() {
        try {
            const response = await fetch('/api/visitor-stats');
            if (response.ok) {
                const stats = await response.json();
                this.displayStats(stats);
                return stats;
            }
        } catch (error) {
            console.error('Error obteniendo estadísticas:', error);
        }
    }

    displayStats(stats) {
        // Actualizar elementos específicos del footer
        const visitorCountElement = document.getElementById('visitor-count');
        const onlineCountElement = document.getElementById('online-count');
        
        if (visitorCountElement && stats) {
            visitorCountElement.textContent = (stats.totalVisitors || 0).toLocaleString();
        }
        
        if (onlineCountElement && stats) {
            onlineCountElement.textContent = (stats.onlineVisitors || 0).toLocaleString();
        }
        
        // También actualizar el elemento de estadísticas completas si existe
        const statsElement = document.getElementById('visitor-stats');
        if (statsElement && stats) {
            statsElement.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-number">${(stats.totalVisitors || 0).toLocaleString()}</span>
                        <span class="stat-label">Total Visitantes</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${(stats.todayVisitors || 0).toLocaleString()}</span>
                        <span class="stat-label">Hoy</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${(stats.onlineVisitors || 0).toLocaleString()}</span>
                        <span class="stat-label">En línea</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${(stats.uniqueVisitors || 0).toLocaleString()}</span>
                        <span class="stat-label">Únicos</span>
                    </div>
                </div>
            `;
        }
        
        console.log('Estadísticas actualizadas:', stats);
    }

    /**
     * 9. RESET DEL CONTADOR (para testing)
     */
    resetCounter() {
        localStorage.removeItem(this.options.storageKey);
        sessionStorage.removeItem(this.options.sessionKey);
        sessionStorage.removeItem('dh2ocol_session_id');
        console.log('Contador reseteado');
        this.displayCounter();
    }
}

// Inicialización automática cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    // Configuración básica
    window.visitorCounter = new VisitorCounter({
        enableAnalytics: true, // Cambiar a false para deshabilitar analytics
        displayElementId: 'visitor-counter'
    });
    
    // Actualizar estadísticas cada 30 segundos
    setInterval(() => {
        if (window.visitorCounter) {
            window.visitorCounter.getServerStats();
        }
    }, 30000);
});

// Funciones globales para uso manual
window.resetVisitorCounter = () => {
    if (window.visitorCounter) {
        window.visitorCounter.resetCounter();
    }
};

window.getVisitorStats = () => {
    if (window.visitorCounter) {
        return window.visitorCounter.getServerStats();
    }
};