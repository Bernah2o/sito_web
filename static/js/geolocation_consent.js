// Geolocalización con consentimiento explícito
(function () {
  const CONSENT_KEY = 'geo_consent_choice'; // 'allow_persistent' | 'deny'
  const COUNTRY_SESSION_KEY = 'geo_country_name';
  const CONSENT_SESSION_KEY = 'geo_consent_session'; // 'allow_session'

  function setText(el, text) {
    if (el) el.textContent = text;
  }

  function updateCountryUI(country) {
    const el = document.getElementById('visitor-country');
    if (country) {
      setText(el, country);
    }
  }

  async function reverseGeocodeCountry(lat, lon) {
    try {
      // Servicio gratuito sin API key
      const url = `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=es`;
      const res = await fetch(url);
      const data = await res.json();
      return data.countryName || data.countryCode || 'Desconocido';
    } catch (e) {
      return 'Desconocido';
    }
  }

  async function requestLocation() {
    if (!('geolocation' in navigator)) {
      return null;
    }
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const { latitude, longitude } = pos.coords;
          const country = await reverseGeocodeCountry(latitude, longitude);
          sessionStorage.setItem(COUNTRY_SESSION_KEY, country);
          updateCountryUI(country);
          resolve(country);
        },
        () => resolve(null),
        { timeout: 8000, enableHighAccuracy: false }
      );
    });
  }

  function createConsentPrompt() {
    const container = document.createElement('div');
    container.className = 'geo-consent';
    container.innerHTML = `
      <div class="geo-box">
        <div class="geo-close" aria-label="Cerrar">✕</div>
        <div class="geo-title"><span>📍</span> Conocer tu ubicación</div>
        <div class="geo-buttons">
          <button class="geo-btn primary" id="geo-allow-session">Permitir mientras se visita el sitio</button>
          <button class="geo-btn secondary" id="geo-allow-once">Permitir esta vez</button>
          <button class="geo-btn danger" id="geo-deny">No permitir nunca</button>
        </div>
      </div>
    `;

    document.body.appendChild(container);

    const close = () => container.remove();
    container.querySelector('.geo-close').addEventListener('click', close);
    container.querySelector('#geo-deny').addEventListener('click', () => {
      localStorage.setItem(CONSENT_KEY, 'deny');
      close();
    });

    container.querySelector('#geo-allow-session').addEventListener('click', async () => {
      sessionStorage.setItem(CONSENT_SESSION_KEY, 'allow_session');
      close();
      await requestLocation();
    });

    container.querySelector('#geo-allow-once').addEventListener('click', async () => {
      close();
      await requestLocation();
    });

    return container;
  }

  async function bootstrap() {
    // Si ya tenemos país en sesión, solo mostrarlo
    const cachedCountry = sessionStorage.getItem(COUNTRY_SESSION_KEY);
    if (cachedCountry) {
      updateCountryUI(cachedCountry);
    }

    // Respeto a decisiones persistentes
    const persistent = localStorage.getItem(CONSENT_KEY);
    if (persistent === 'deny') {
      return; // No molestar
    }

    if (persistent === 'allow_persistent') {
      await requestLocation();
      return;
    }

    // Permiso por sesión ya otorgado
    if (sessionStorage.getItem(CONSENT_SESSION_KEY) === 'allow_session') {
      await requestLocation();
      return;
    }

    // Mostrar prompt personalizado; el navegador renderizará su propio diálogo de permisos.
    const prompt = createConsentPrompt();
    // Si quieres guardar consentimiento persistente, podrías añadir un checkbox.
  }

  document.addEventListener('DOMContentLoaded', bootstrap);
})();