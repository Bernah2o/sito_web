// Botón flotante de WhatsApp en todas las páginas
document.addEventListener('DOMContentLoaded', () => {
  try {
    if (document.getElementById('whatsapp-float')) return;

    const link = document.createElement('a');
    link.href = '/whatsapp';
    link.id = 'whatsapp-float';
    link.className = 'whatsapp-float';
    link.title = 'Chatea con nosotros por WhatsApp';
    link.setAttribute('aria-label', 'Chatea con nosotros por WhatsApp');

    // Detectar si Font Awesome está presente, si no, usar texto "WA" como fallback
    const hasFA = !!document.querySelector(
      'link[href*="fontawesome"], link[href*="font-awesome"], link[href*="fontawesome.com"]'
    );
    if (hasFA) {
      link.innerHTML = '<i class="fab fa-whatsapp" aria-hidden="true"></i>';
    } else {
      const span = document.createElement('span');
      span.textContent = 'WA';
      span.className = 'wa-fallback';
      link.appendChild(span);
    }

    // Respetar preferencias de movimiento reducido; si no, activar pulso
    const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduceMotion) {
      link.classList.add('pulse');
    }

    document.body.appendChild(link);
  } catch (e) {
    console.error('Error creando botón WhatsApp:', e);
  }
});