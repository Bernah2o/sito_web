// DH2O Quote Wizard JS
(function() {
  const modal = document.getElementById('cotizacionWizardModal');
  if (!modal) return;

  // Lightweight custom dialog to replace window.alert/confirm
  function showDialog({ title = 'Mensaje', message = '', okText = 'Aceptar', cancelText = null, type = 'info' } = {}) {
    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'dw-dialog-overlay';
      const box = document.createElement('div');
      box.className = 'dw-dialog';

      const header = document.createElement('div');
      header.className = 'dw-dialog-header';
      const icon = document.createElement('span');
      icon.className = 'dw-icon';
      icon.textContent = type === 'success' ? '✔' : type === 'error' ? '⚠' : 'ℹ';
      const ttl = document.createElement('div');
      ttl.className = 'dw-title';
      ttl.textContent = title;
      header.appendChild(icon);
      header.appendChild(ttl);

      const body = document.createElement('div');
      body.className = 'dw-dialog-body';
      body.textContent = message;

      const actions = document.createElement('div');
      actions.className = 'dw-dialog-actions';
      const okBtn = document.createElement('button');
      okBtn.className = 'dw-btn dw-btn-primary';
      okBtn.textContent = okText || 'Aceptar';
      okBtn.addEventListener('click', () => { document.body.removeChild(overlay); resolve(true); });
      actions.appendChild(okBtn);
      if (cancelText) {
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'dw-btn dw-btn-secondary';
        cancelBtn.textContent = cancelText;
        cancelBtn.addEventListener('click', () => { document.body.removeChild(overlay); resolve(false); });
        actions.appendChild(cancelBtn);
      }

      box.appendChild(header);
      box.appendChild(body);
      box.appendChild(actions);
      overlay.appendChild(box);
      overlay.addEventListener('click', (e) => { if (e.target === overlay) { document.body.removeChild(overlay); resolve(false); } });
      document.body.appendChild(overlay);
    });
  }

  function showAlert(message, { title = 'Mensaje', type = 'info', okText = 'Aceptar' } = {}) {
    return showDialog({ title, message, okText, type });
  }

  function showConfirm(message, { title = 'Confirmar', okText = 'Aceptar', cancelText = 'Cancelar', type = 'info' } = {}) {
    return showDialog({ title, message, okText, cancelText, type });
  }

  // State
  const state = {
    step: 1,
    servicio: null,
    datos: {},
    imageUrls: [],
    imageUrlsBySource: { reparacion: [], instalacion: [] }
  };

  // Elements
  const steps = modal.querySelectorAll('.wizard-step');
  const panes = modal.querySelectorAll('.wizard-pane');
  const nextBtn = modal.querySelector('#nextStep');
  const prevBtn = modal.querySelector('#prevStep');
  const serviceButtons = modal.querySelectorAll('.service-option');
  const quoteValueEl = modal.querySelector('#quote-value');
  const quoteTimeEl = modal.querySelector('#quote-time');
  const quoteServiceLabelEl = modal.querySelector('#quote-service-label');
  const sendWhatsappBtn = modal.querySelector('#sendWhatsapp');
  const sendEmailBtn = modal.querySelector('#sendEmail');
  const ubicacionBtn = modal.querySelector('#btnUbicacionMapa');
  const politicaCheckbox = modal.querySelector('#aceptaPolitica');
  const telefonoInput = modal.querySelector('#telefonoCliente');

  // Validación de campos obligatorios
  function validateRequired() {
    const errores = [];
    const nombre = (state.datos.nombreCliente || '').trim();
    const telefono = (state.datos.telefonoCliente || '').trim();
    const acepta = !!politicaCheckbox?.checked;

    if (!nombre) errores.push('Nombre');
    if (!telefono) errores.push('Teléfono (WhatsApp)');
    if (!acepta) errores.push('Aceptar la Política de Privacidad');

    if (errores.length) {
      const mensaje = 'Debes completar: ' + errores.join(', ') + '.';
      showAlert(mensaje, { title: 'Datos necesarios', type: 'error' });
      return false;
    }
    return true;
  }

  // ===== Validación por pasos =====
  function markFieldValidity(id, valid) {
    const el = modal.querySelector(`#${id}`);
    if (!el) return;
    el.classList.toggle('input-invalid', !valid);
    el.classList.toggle('input-valid', !!valid);
  }

  function getValue(id) {
    const v = state.datos[id];
    if (typeof v === 'boolean') return v ? '1' : '';
    return (v || '').toString().trim();
  }

  function requireFields(ids, labelsMap = {}) {
    const missing = [];
    ids.forEach(id => {
      const val = getValue(id);
      const ok = !!val;
      markFieldValidity(id, ok);
      if (!ok) missing.push(labelsMap[id] || id);
    });
    return missing;
  }

  function validateStep(step) {
    const labels = {
      tipoTanque: 'Tipo de tanque',
      capacidadTanque: 'Capacidad del tanque',
      accesibilidad: 'Nivel de accesibilidad',
      tipoDano: 'Tipo de daño',
      descripcionOtro: 'Descripción',
      barrio: 'Barrio',
      ciudad: 'Ciudad',
      direccion: 'Dirección',
      referencia: 'Referencia',
      nombreCliente: 'Nombre',
      telefonoCliente: 'Teléfono (WhatsApp)'
    };

    if (step === 1) {
      if (!state.servicio) {
        showAlert('Selecciona un tipo de servicio para continuar.', { title: 'Servicio requerido', type: 'error' });
        return false;
      }
      return true;
    }

    if (step === 2) {
      let required = [];
      if (state.servicio === 'limpieza' || state.servicio === 'instalacion') {
        required = ['tipoTanque', 'capacidadTanque', 'accesibilidad'];
      } else if (state.servicio === 'reparacion') {
        required = ['tipoDano'];
      } else {
        required = ['descripcionOtro'];
      }
      const miss = requireFields(required, labels);
      // Validación específica de capacidad
      if (required.includes('capacidadTanque')) {
        const cap = Number(getValue('capacidadTanque'));
        const capOk = cap > 0;
        markFieldValidity('capacidadTanque', capOk);
        if (!capOk && !miss.includes(labels['capacidadTanque'])) miss.push(labels['capacidadTanque']);
      }
      if (miss.length) {
        showAlert('Completa: ' + miss.join(', ') + '.', { title: 'Datos requeridos', type: 'error' });
        return false;
      }
      return true;
    }

    if (step === 3) {
      const miss = requireFields(['barrio', 'ciudad', 'direccion'], labels);
      if (miss.length) {
        showAlert('Indica tu ubicación: ' + miss.join(', ') + '.', { title: 'Ubicación requerida', type: 'error' });
        return false;
      }
      return true;
    }

    if (step === 4) {
      // Usa la validación de cliente existente, incluyendo teléfono y política
      return validateRequired();
    }

    return true;
  }

  // Helpers
  function setStep(n) {
    state.step = n;
    steps.forEach(s => s.classList.toggle('active', Number(s.dataset.step) === n));
    panes.forEach(p => p.classList.toggle('d-none', Number(p.dataset.step) !== n));
    prevBtn.disabled = n === 1;
    nextBtn.textContent = n === 5 ? 'Finalizar' : 'Siguiente';
    // Show send buttons on step 5
    sendWhatsappBtn.classList.toggle('d-none', n !== 5);
    sendEmailBtn.classList.toggle('d-none', n !== 5);
  }

  function formatCOP(value) {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);
  }
  // Formato y validación de teléfono Colombia (WhatsApp)
  function digitsOnly(v) { return (v || '').replace(/\D+/g, ''); }
  function normalizePhoneCO(v) {
    let d = digitsOnly(v);
    if (d.startsWith('57') && d.length === 12) d = d.slice(2);
    return d;
  }
  function isValidWhatsAppCO(v) {
    const d = normalizePhoneCO(v);
    return d.length === 10 && d.startsWith('3');
  }
  function formatPhoneCO(v) {
    const d = normalizePhoneCO(v);
    if (!d) return '';
    if (d.length <= 3) return d;
    if (d.length <= 6) return `${d.slice(0,3)} ${d.slice(3)}`;
    return `${d.slice(0,3)} ${d.slice(3,6)} ${d.slice(6,10)}`;
  }

  // Params fetched from backend to allow admin configuration
  let pricingParams = null;

  function basePricing(servicio) {
    switch (servicio) {
      case 'limpieza': return { base: Number(pricingParams?.quote_base_limpieza || 70000), hours: Number(pricingParams?.quote_hours_limpieza || 0.75) };
      case 'reparacion': return { base: Number(pricingParams?.quote_base_reparacion || 100000), hours: Number(pricingParams?.quote_hours_reparacion || 1) };
      case 'instalacion': return { base: Number(pricingParams?.quote_base_instalacion || 150000), hours: Number(pricingParams?.quote_hours_instalacion || 4) };
      case 'inspeccion': return { base: Number(pricingParams?.quote_base_inspeccion || 50000), hours: Number(pricingParams?.quote_hours_inspeccion || 0.25) };
      default: return { base: Number(pricingParams?.quote_base_otro || 100000), hours: Number(pricingParams?.quote_hours_otro || 2) };
    }
  }

  function computeEstimate() {
    if (!state.servicio) return { valor: 0, horas: '-' };
    const { base, hours } = basePricing(state.servicio);
    let factor = 1.0;

    if (state.servicio === 'limpieza' || state.servicio === 'instalacion') {
      const tipo = state.datos.tipoTanque || 'plastico';
      const capacidad = Number(state.datos.capacidadTanque) || 250;
      const acces = state.datos.accesibilidad || 'facil';

      const tipoFactor = { plastico: 1, fibra: 1.1, metalico: 1.2, elevado: 1.15, subterraneo: 1.25 }[tipo] || 1;
      const capFactor = capacidad <= 250 ? 1 : capacidad <= 500 ? 1.2 : capacidad <= 1000 ? 1.5 : capacidad <= 2000 ? 2.0 : 2.5;
      const accFactor = { facil: 1, media: 1.15, dificil: 1.3 }[acces] || 1;

      factor *= tipoFactor * capFactor * accFactor;
      if (state.servicio === 'instalacion' && state.datos.requiereEstructura === 'si') factor *= 1.3;
    }

    if (state.servicio === 'reparacion') {
      const dano = state.datos.tipoDano || 'fuga';
      const danoFactor = { fuga: 1.1, fisura: 1.2, corrosion: 1.3, valvulas: 1.15, otro: 1.1 }[dano] || 1.1;
      factor *= danoFactor;
    }

    if (state.servicio === 'inspeccion') {
      // Dron: más simple, pequeños ajustes si descripción indica difícil acceso (heurística básica)
      const desc = (state.datos.descripcionOtro || '').toLowerCase();
      if (desc.includes('difícil') || desc.includes('dificil') || desc.includes('alto')) factor *= 1.15;
    }

    const valor = Math.round(base * factor);
    const timeFactor = state.servicio === 'inspeccion' ? 1.0 : 0.8;
    const totalHours = hours * factor * timeFactor;
    let tiempoStr;
    if (state.servicio === 'inspeccion') {
      const minutos = Math.round(totalHours * 60);
      tiempoStr = minutos < 60 ? `${minutos} min` : `${Math.round(minutos / 60)} h`;
    } else {
      tiempoStr = `${Math.round(totalHours)} h`;
    }
    return { valor, horas: tiempoStr };
  }

  function updateQuoteUI() {
    const est = computeEstimate();
    quoteValueEl.textContent = formatCOP(est.valor);
    quoteTimeEl.textContent = `Tiempo estimado: ${est.horas}`;
    const labelMap = { limpieza: 'Limpieza', reparacion: 'Reparación', instalacion: 'Instalación', inspeccion: 'Inspección con dron', otro: 'Otro' };
    quoteServiceLabelEl.textContent = labelMap[state.servicio] || 'Servicio';
    const noteEl = modal.querySelector('#quote-note');
    if (noteEl) {
      const base = 'Nota: El valor final puede variar tras revisión en sitio.';
      const extra = (state.servicio === 'instalacion' && state.datos.requiereEstructura === 'si') || (state.servicio === 'reparacion')
        ? ' No incluye accesorios ni materiales cuando se requiere de estructura.'
        : '';
      noteEl.textContent = base + extra;
    }
  }

  function collectStepData() {
    // Gather visible inputs of current step
    const pane = modal.querySelector(`.wizard-pane[data-step="${state.step}"]`);
    pane.querySelectorAll('input, select, textarea').forEach(el => {
      if (el.id) state.datos[el.id.replace('Tanque','Tanque').replace('Cliente','Cliente')] = el.type === 'checkbox' ? el.checked : el.value;
    });
  }

  function showServiceFields() {
    const groups = modal.querySelectorAll('.service-fields');
    groups.forEach(g => {
      const services = (g.dataset.service || '').split(' ');
      g.classList.toggle('d-none', !services.includes(state.servicio));
    });
  }

  function buildMessage(opts = {}) {
    const includeImageUrls = opts.includeImageUrls !== false;
    const est = computeEstimate();
    const nombre = state.datos.nombreCliente || '';
    const tel = state.datos.telefonoCliente || '';
    const correo = state.datos.correoCliente || '';
    const barrio = state.datos.barrio || '';
    const ciudad = state.datos.ciudad || 'Valledupar';
    const dir = state.datos.direccion || '';
    const ref = state.datos.referencia || '';
    const mapa = state.datos.ubicacionMapa || '';

    const labelMap = { limpieza: 'Limpieza de tanque', reparacion: 'Reparación', instalacion: 'Instalación', inspeccion: 'Inspección con dron', otro: 'Otro' };
    const servicioLabel = labelMap[state.servicio] || 'Servicio';

    const detalles = [];
    if (state.servicio === 'limpieza' || state.servicio === 'instalacion') {
      detalles.push(`Tipo de tanque: ${state.datos.tipoTanque || ''}`);
      detalles.push(`Capacidad: ${state.datos.capacidadTanque || ''} L`);
      if (state.datos.alturaTanque) detalles.push(`Altura: ${state.datos.alturaTanque} m`);
      if (state.datos.accesibilidad) detalles.push(`Accesibilidad: ${state.datos.accesibilidad}`);
      if (state.servicio === 'instalacion') detalles.push(`Estructura nueva: ${state.datos.requiereEstructura || 'no'}`);
    }
    if (state.servicio === 'reparacion') {
      detalles.push(`Daño: ${state.datos.tipoDano || ''}`);
    }
    if (state.servicio === 'inspeccion' || state.servicio === 'otro') {
      if (state.datos.descripcionOtro) detalles.push(`Descripción: ${state.datos.descripcionOtro}`);
    }

    const mapaStr = mapa ? `\nMapa: ${mapa}` : '';
    const imagenesStr = includeImageUrls && Array.isArray(state.imageUrls) && state.imageUrls.length
      ? `\nImágenes:\n${state.imageUrls.map((u, i) => `${i + 1}. ${u}`).join('\n')}`
      : '';
    const extraNota = (state.servicio === 'instalacion' || state.servicio === 'reparacion')
      ? ' No incluye accesorios ni materiales cuando se requiere de estructura.'
      : '';
    const texto = `Hola DH2OCOL, solicito una cotización.\n\n` +
      `Servicio: ${servicioLabel}\n` +
      `${detalles.join('\n')}\n\n` +
      `Ubicación: ${barrio}, ${ciudad}. Dir: ${dir}. Ref: ${ref}${mapaStr}${imagenesStr}\n` +
      `Cliente: ${nombre}. Tel: ${tel}. Correo: ${correo}\n\n` +
      `Estimado: ${formatCOP(est.valor)} | Tiempo: ${est.horas}\n` +
      `Nota: El valor final puede variar tras revisión en sitio.${extraNota}`;
    return texto;
  }

  function updateSendLinks() {
    const message = encodeURIComponent(buildMessage({ includeImageUrls: false }));
    const phone = (window.DH2O_WHATSAPP || '573157484662').replace(/\D/g,'');
    sendWhatsappBtn.href = `https://wa.me/${phone}?text=${message}`;
    // Email se enviará vía backend para soportar imágenes adjuntas
  }

  // Geolocalización para ubicación en el mapa
  if (ubicacionBtn) {
    ubicacionBtn.addEventListener('click', async () => {
      try {
        if (!navigator.geolocation) {
          await showAlert('Tu navegador no soporta geolocalización. Puedes pegar un enlace de Google Maps manualmente.', { title: 'Ubicación', type: 'info' });
          return;
        }
        ubicacionBtn.disabled = true;
        ubicacionBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Obteniendo ubicación...';
        navigator.geolocation.getCurrentPosition((pos) => {
          const { latitude, longitude } = pos.coords;
          const mapsLink = `https://www.google.com/maps?q=${latitude},${longitude}`;
          const input = modal.querySelector('#ubicacionMapa');
          if (input) input.value = mapsLink;
          state.datos['ubicacionMapa'] = mapsLink;
          ubicacionBtn.innerHTML = '<i class="fas fa-location-crosshairs me-1"></i>Compartir mi ubicación';
          ubicacionBtn.disabled = false;
          updateQuoteUI();
          updateSendLinks();
        }, (err) => {
          showAlert('No se pudo obtener la ubicación. Verifica permisos y GPS.', { title: 'Ubicación', type: 'error' });
          ubicacionBtn.innerHTML = '<i class="fas fa-location-crosshairs me-1"></i>Compartir mi ubicación';
          ubicacionBtn.disabled = false;
        }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
      } catch (e) {
        ubicacionBtn.innerHTML = '<i class="fas fa-location-crosshairs me-1"></i>Compartir mi ubicación';
        ubicacionBtn.disabled = false;
      }
    });
  }

  // Subida de imágenes a backend (Firebase) para incluir enlaces en WhatsApp y adjuntar en email
  async function uploadQuoteImages() {
    const files = [];
    const reparacionInput = modal.querySelector('#fotosReparacion');
    const instalacionInput = modal.querySelector('#fotosInstalacion');
    if (reparacionInput && reparacionInput.files?.length) files.push(...reparacionInput.files);
    if (instalacionInput && instalacionInput.files?.length) files.push(...instalacionInput.files);
    if (!files.length) return [];

    const formData = new FormData();
    files.forEach(f => formData.append('images', f));
    // Subir a carpeta Firebase 'cotizaciones' para compartir en correo/WhatsApp
    formData.append('folder', 'cotizaciones');
    const res = await fetch('/api/quote/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (data?.success && Array.isArray(data.urls)) {
      return data.urls;
    }
    return [];
  }

  // Mostrar/ocultar barra de progreso para inputs de imágenes
  function setUploadProgress(which, active, text) {
    const bar = modal.querySelector(`#progress${which}`);
    const label = modal.querySelector(`#progress${which}Text`);
    if (!bar) return;
    bar.classList.toggle('d-none', !active);
    if (label && text) label.textContent = text;
  }

  // Renderizar miniaturas debajo del input correspondiente
  function renderImagePreviews(which, urls) {
    const containerId = which === 'Reparacion' ? 'previewReparacion' : 'previewInstalacion';
    const container = modal.querySelector(`#${containerId}`);
    if (!container) return;
    const list = Array.isArray(urls) ? urls : [];
    if (!list.length) {
      container.classList.add('d-none');
      container.innerHTML = '';
      return;
    }
    container.classList.remove('d-none');
    const sourceKey = which === 'Reparacion' ? 'reparacion' : 'instalacion';
    container.innerHTML = list.map((u) => {
      const safe = String(u);
      return `
        <div class="thumb" data-url="${safe}">
          <button class="del-btn" title="Eliminar" data-url="${safe}" data-src="${sourceKey}">×</button>
          <a href="${safe}" target="_blank" rel="noopener noreferrer"><img src="${safe}" alt="imagen" loading="lazy"></a>
        </div>`;
    }).join('');
  }

  // Renderizar miniaturas locales (blob:) para selección previa al upload
  function renderLocalImagePreviews(which, inputEl) {
    const containerId = which === 'Reparacion' ? 'previewReparacion' : 'previewInstalacion';
    const container = modal.querySelector(`#${containerId}`);
    if (!container) return;
    const files = inputEl?.files ? Array.from(inputEl.files) : [];
    if (!files.length) {
      container.classList.add('d-none');
      container.innerHTML = '';
      return;
    }
    container.classList.remove('d-none');
    const sourceKey = which === 'Reparacion' ? 'reparacion' : 'instalacion';
    container.innerHTML = files.map((f, i) => {
      const blobUrl = URL.createObjectURL(f);
      return `
        <div class="thumb" data-url="${blobUrl}">
          <button class="del-btn" title="Quitar" data-local="1" data-index="${i}" data-src="${sourceKey}">×</button>
          <a href="${blobUrl}" target="_blank" rel="noopener noreferrer"><img src="${blobUrl}" alt="imagen" loading="lazy"></a>
        </div>`;
    }).join('');
  }

  // Diálogo de confirmación personalizado (usa estilos dw-dialog-* en CSS)
  function showConfirm(message, opts = {}) {
    return new Promise((resolve) => {
      const title = opts.title || 'Confirmación';
      const overlay = document.createElement('div');
      overlay.className = 'dw-dialog-overlay';
      overlay.innerHTML = `
        <div class="dw-dialog" role="dialog" aria-modal="true">
          <div class="dw-dialog-header"><span class="dw-title">${title}</span></div>
          <div class="dw-dialog-body">${message}</div>
          <div class="dw-dialog-actions">
            <button class="dw-btn dw-btn-secondary" data-action="cancel">Cancelar</button>
            <button class="dw-btn dw-btn-primary" data-action="ok">Aceptar</button>
          </div>
        </div>`;
      // Mostrar dentro de la modal principal para mantener contexto
      modal.appendChild(overlay);

      let done = false;
      const cleanup = (val) => {
        if (done) return;
        done = true;
        overlay.remove();
        modal.removeEventListener('keydown', onKey);
        resolve(val);
      };
      const onKey = (e) => { if (e.key === 'Escape') cleanup(false); };
      modal.addEventListener('keydown', onKey);

      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) cleanup(false);
      });
      overlay.querySelector('[data-action="cancel"]').addEventListener('click', () => cleanup(false));
      overlay.querySelector('[data-action="ok"]').addEventListener('click', () => cleanup(true));
    });
  }

  // Eliminar imagen: confirmación, backend + estado y miniaturas con overlay
  async function deleteImage(url, sourceKey, btnEl) {
    // Confirmar con el usuario
    const confirmed = await showConfirm('¿Eliminar esta imagen de tu cotización?', { title: 'Confirmar eliminación' });
    if (!confirmed) return;

    // Mostrar overlay de estado y deshabilitar botón
    let overlay;
    try {
      if (btnEl) {
        btnEl.disabled = true;
        const thumb = btnEl.closest('.thumb');
        if (thumb) {
          overlay = document.createElement('div');
          overlay.className = 'status-overlay';
          overlay.innerHTML = '<span>Eliminando...</span>';
          thumb.appendChild(overlay);
        }
      }

      const res = await fetch('/api/quote/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await res.json();
      if (!data?.success) throw new Error('No se pudo eliminar');

      // Actualizar estado
      state.imageUrls = (state.imageUrls || []).filter(u => u !== url);
      const arr = Array.isArray(state.imageUrlsBySource[sourceKey]) ? state.imageUrlsBySource[sourceKey] : [];
      state.imageUrlsBySource[sourceKey] = arr.filter(u => u !== url);
      // Re-render de miniaturas
      renderImagePreviews('Reparacion', state.imageUrlsBySource.reparacion);
      renderImagePreviews('Instalacion', state.imageUrlsBySource.instalacion);
      updateSendLinks();
    } catch (err) {
      await showAlert('No se pudo eliminar la imagen. Intenta nuevamente.', { title: 'Eliminar imagen', type: 'error' });
    } finally {
      if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
      if (btnEl) btnEl.disabled = false;
    }
  }

  // Subir imágenes inmediatamente cuando el usuario las seleccione
  async function uploadImagesForInput(inputId) {
    const input = modal.querySelector(`#${inputId}`);
    if (!input || !input.files?.length) return;
    const which = inputId === 'fotosReparacion' ? 'Reparacion' : 'Instalacion';
    const key = inputId === 'fotosReparacion' ? 'reparacion' : 'instalacion';
    try {
      input.disabled = true;
      setUploadProgress(which, true, 'Subiendo imágenes...');
      const formData = new FormData();
      Array.from(input.files).forEach(f => formData.append('images', f));
      formData.append('folder', 'cotizaciones');
      const res = await fetch('/api/quote/upload', { method: 'POST', body: formData });
      const data = await res.json();
      if (data?.success && Array.isArray(data.urls)) {
        const current = Array.isArray(state.imageUrls) ? state.imageUrls : [];
        // Concatenar y evitar duplicados
        const merged = [...current, ...data.urls];
        state.imageUrls = Array.from(new Set(merged));
        const srcCurrent = Array.isArray(state.imageUrlsBySource[key]) ? state.imageUrlsBySource[key] : [];
        state.imageUrlsBySource[key] = Array.from(new Set([...srcCurrent, ...data.urls]));
        renderImagePreviews(which, state.imageUrlsBySource[key]);
        updateQuoteUI();
        updateSendLinks();
        setUploadProgress(which, true, `Imágenes subidas (${data.urls.length}).`);
        // Ocultar la barra después de un breve tiempo
        setTimeout(() => setUploadProgress(which, false), 1200);
      } else {
        setUploadProgress(which, true, 'No se pudieron subir las imágenes.');
        setTimeout(() => setUploadProgress(which, false), 2000);
      }
    } catch (err) {
      setUploadProgress(which, true, 'Error al subir imágenes.');
      setTimeout(() => setUploadProgress(which, false), 2000);
    } finally {
      input.disabled = false;
    }
  }

  async function finalizeStep() {
    // Validar requeridos (nombre, teléfono y política)
    if (!validateRequired()) return;
    // Validar formato de teléfono Colombia
    const tel = (state.datos.telefonoCliente || '').trim();
    if (!isValidWhatsAppCO(tel)) {
      showAlert('Ingresa un teléfono móvil de Colombia válido (empieza por 3 y tiene 10 dígitos).', { title: 'Teléfono inválido', type: 'error' });
      return;
    }
    // Solo cerrar la modal, sin subir imágenes
    nextBtn.disabled = true;
    nextBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Finalizando...';
    try {
      updateQuoteUI();
      updateSendLinks();
      // Cerrar la modal
      try {
        const inst = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
        inst.hide();
      } catch (_) {}
    } finally {
      nextBtn.disabled = false;
      nextBtn.innerHTML = 'Finalizar';
    }
  }

  // Event: select service
  serviceButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      serviceButtons.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      state.servicio = btn.dataset.service;
      showServiceFields();
      setStep(2);
      updateQuoteUI();
    });
  });

  // Nav buttons
  nextBtn.addEventListener('click', async () => {
    collectStepData();
    if (state.step < 5) {
      if (!validateStep(state.step)) return;
      setStep(state.step + 1);
    } else {
      // Antes de finalizar, garantizar que el paso 4 esté correcto
      if (!validateStep(4)) return;
      await finalizeStep();
    }
  });
  prevBtn.addEventListener('click', () => {
    if (state.step > 1) setStep(state.step - 1);
  });

  // Live updates for inputs
  modal.addEventListener('input', (e) => {
    const el = e.target;
    if (!el.id) return;
    if (el.id === 'telefonoCliente') {
      const formatted = formatPhoneCO(el.value);
      el.value = formatted;
      const valid = isValidWhatsAppCO(formatted);
      el.classList.toggle('input-invalid', !valid && digitsOnly(formatted).length > 0);
      el.classList.toggle('input-valid', valid);
    }
    state.datos[el.id] = el.value;
    updateQuoteUI();
    updateSendLinks();
  });

  // Detectar selección de imágenes y mostrar miniaturas locales (sin subir todavía)
  ['fotosReparacion', 'fotosInstalacion'].forEach(id => {
    const input = modal.querySelector(`#${id}`);
    if (input) {
      input.addEventListener('change', () => {
        if (input.files && input.files.length) {
          const which = id === 'fotosReparacion' ? 'Reparacion' : 'Instalacion';
          renderLocalImagePreviews(which, input);
        } else {
          const which = id === 'fotosReparacion' ? 'Reparacion' : 'Instalacion';
          const containerId = which === 'Reparacion' ? 'previewReparacion' : 'previewInstalacion';
          const c = modal.querySelector(`#${containerId}`);
          if (c) { c.innerHTML = ''; c.classList.add('d-none'); }
        }
      });
    }
  });

  // Delegación para botón eliminar en miniaturas
  modal.addEventListener('click', async (e) => {
    const btn = e.target.closest('.del-btn');
    if (!btn) return;
    e.preventDefault();
    const isLocal = btn.dataset.local === '1';
    const src = btn.dataset.src; // 'reparacion' | 'instalacion'
    if (isLocal) {
      // Remover archivo del input correspondiente
      const inputId = src === 'reparacion' ? 'fotosReparacion' : 'fotosInstalacion';
      const input = modal.querySelector(`#${inputId}`);
      const idx = parseInt(btn.dataset.index || '-1', 10);
      if (input && input.files && idx >= 0) {
        const confirmed = await showConfirm('¿Quitar esta imagen de tu selección?', { title: 'Confirmar' });
        if (!confirmed) return;
        const dt = new DataTransfer();
        Array.from(input.files).forEach((f, i) => { if (i !== idx) dt.items.add(f); });
        input.files = dt.files;
        const which = inputId === 'fotosReparacion' ? 'Reparacion' : 'Instalacion';
        renderLocalImagePreviews(which, input);
      }
      return;
    }
    const url = btn.dataset.url;
    if (url && src) deleteImage(url, src, btn);
  });

  // When modal opens, reset state
  modal.addEventListener('shown.bs.modal', () => {
    state.step = 1; state.servicio = null; state.datos = {};
    state.imageUrls = [];
    state.imageUrlsBySource = { reparacion: [], instalacion: [] };
    steps.forEach(s => s.classList.remove('active'));
    panes.forEach(p => p.classList.add('d-none'));
    modal.querySelector('.wizard-pane[data-step="1"]').classList.remove('d-none');
    modal.querySelector('.wizard-step[data-step="1"]').classList.add('active');
    sendWhatsappBtn.classList.add('d-none');
    sendEmailBtn.classList.add('d-none');
    prevBtn.disabled = true;
    nextBtn.textContent = 'Siguiente';
    // Limpiar estados visuales
    modal.querySelectorAll('input, select, textarea').forEach(el => {
      el.classList.remove('input-invalid', 'input-valid');
    });
    // Limpiar miniaturas
    ['previewReparacion', 'previewInstalacion'].forEach(id => {
      const c = modal.querySelector(`#${id}`);
      if (c) { c.innerHTML = ''; c.classList.add('d-none'); }
    });
    updateQuoteUI();
    // Fetch pricing params from backend
    fetch('/api/quote/params').then(r => r.json()).then(d => { if (d?.success) pricingParams = d.params; });
  });

  // Envío por correo vía backend (con adjuntos)
  sendEmailBtn.addEventListener('click', async () => {
    try {
      // Validar requeridos antes de enviar
      if (!validateRequired()) return;
      const tel = (state.datos.telefonoCliente || '').trim();
      if (!isValidWhatsAppCO(tel)) {
        showAlert('Ingresa un teléfono móvil de Colombia válido (empieza por 3 y tiene 10 dígitos).', { title: 'Teléfono inválido', type: 'error' });
        return;
      }
      // Asegurar que las imágenes se suban antes de enviar
      if (!state.imageUrls || !state.imageUrls.length) {
        try {
          state.imageUrls = await uploadQuoteImages();
        } catch (err) {
          console.warn('No se pudo subir imágenes antes del correo:', err);
        }
      }
      sendEmailBtn.disabled = true;
      sendEmailBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';
      const payload = {
        servicio: state.servicio,
        datos: state.datos,
        estimate: computeEstimate(),
        image_urls: state.imageUrls || []
      };

      // Ejecutar reCAPTCHA v3 si está disponible en la página
      try {
        if (typeof grecaptcha !== 'undefined' && window.recaptchaSiteKey) {
          const token = await grecaptcha.execute(window.recaptchaSiteKey, { action: 'quote_email' });
          if (token) payload.recaptcha_token = token;
        }
      } catch (err) {
        console.warn('reCAPTCHA no disponible o falló:', err);
      }

      const res = await fetch('/api/quote/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data?.success) {
        await showAlert('Se envió tu cotización por correo. ¡Gracias!', { title: 'Envío de cotización', type: 'success' });
      } else {
        await showAlert('No se pudo enviar el correo. Intenta nuevamente.', { title: 'Envío de cotización', type: 'error' });
      }
    } catch (e) {
      await showAlert('Error al enviar el correo.', { title: 'Envío de cotización', type: 'error' });
    } finally {
      sendEmailBtn.disabled = false;
      sendEmailBtn.innerHTML = '<i class="fas fa-envelope me-2"></i>Enviar por correo';
    }
  });

  // Enviar por WhatsApp como solo texto usando wa.me (sin imágenes)
  sendWhatsappBtn.addEventListener('click', async (e) => {
    if (!validateRequired()) { e.preventDefault(); return; }
    const tel = (state.datos.telefonoCliente || '').trim();
    if (!isValidWhatsAppCO(tel)) {
      e.preventDefault();
      await showAlert('Ingresa un teléfono móvil de Colombia válido (empieza por 3 y tiene 10 dígitos).', { title: 'Teléfono inválido', type: 'error' });
      return;
    }
    // No prevenir el comportamiento por defecto: abrirá el enlace wa.me con el texto
  });
})();