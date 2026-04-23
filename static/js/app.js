/* ============================================================
   ESTACIONAMIENTO PÚBLICO — Main JavaScript
   Full CRUD operations + UI interactions
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initModals();
  initTabs();
  initFlashMessages();
  initAnimations();
  initSearch();
});

/* ============================================================
   SIDEBAR — Mobile Toggle
   ============================================================ */
function initSidebar() {
  const menuBtn = document.getElementById('mobile-menu-btn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('active');
    });
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('active');
    });
  }
}

/* ============================================================
   MODALS
   ============================================================ */
function initModals() {
  document.querySelectorAll('[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-modal');
      openModal(modalId);
    });
  });

  document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const overlay = btn.closest('.modal-overlay');
      if (overlay) closeModal(overlay.id);
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
    // Reset forms inside
    const form = modal.querySelector('form');
    if (form) form.reset();
  }
}

/* ============================================================
   TABS
   ============================================================ */
function initTabs() {
  document.querySelectorAll('.tabs').forEach(tabGroup => {
    const tabs = tabGroup.querySelectorAll('.tab-item');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const target = tab.getAttribute('data-tab');
        const parent = tab.closest('.content-card') || tab.closest('.main-body') || document.body;
        tabGroup.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
        parent.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const targetContent = parent.querySelector(`#${target}`) || document.getElementById(target);
        if (targetContent) targetContent.classList.add('active');
      });
    });
  });
}

/* ============================================================
   FLASH MESSAGES / TOASTS
   ============================================================ */
function initFlashMessages() {
  document.querySelectorAll('.flash-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const msg = btn.closest('.flash-msg');
      msg.style.animation = 'toastSlide 0.3s ease reverse';
      setTimeout(() => msg.remove(), 300);
    });
  });

  document.querySelectorAll('.flash-msg').forEach(msg => {
    setTimeout(() => {
      if (msg.parentNode) {
        msg.style.opacity = '0';
        msg.style.transform = 'translateX(100px)';
        msg.style.transition = 'all 0.3s ease';
        setTimeout(() => msg.remove(), 300);
      }
    }, 5000);
  });
}

function showToast(message, type = 'success') {
  let container = document.querySelector('.flash-messages');
  if (!container) {
    container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `flash-msg ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✅' : '❌'}</span>
    <span>${message}</span>
    <button class="flash-close" onclick="this.closest('.flash-msg').remove()">✕</button>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }
  }, 5000);
}

/* ============================================================
   ANIMATIONS
   ============================================================ */
function initAnimations() {
  document.querySelectorAll('.stat-card-value[data-count]').forEach(el => {
    const target = parseInt(el.getAttribute('data-count'));
    if (!isNaN(target)) animateCount(el, 0, target, 1000);
  });

  setTimeout(() => {
    document.querySelectorAll('.bar-chart-bar[data-height]').forEach(bar => {
      bar.style.height = bar.getAttribute('data-height');
    });
  }, 300);
}

function animateCount(el, start, end, duration) {
  const range = end - start;
  const startTime = performance.now();
  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + range * eased);
    el.textContent = current.toLocaleString();
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* ============================================================
   SEARCH — Tables
   ============================================================ */
function initSearch() {
  document.querySelectorAll('[data-search-table]').forEach(input => {
    const tableId = input.getAttribute('data-search-table');
    const table = document.getElementById(tableId);
    if (!table) return;
    input.addEventListener('input', () => {
      const query = input.value.toLowerCase();
      table.querySelectorAll('tbody tr').forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
      });
    });
  });
}


/* ============================================================
   GENERIC CRUD HELPERS
   ============================================================ */

function apiRequest(url, method, data = null) {
  const options = {
    method: method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (data) options.body = JSON.stringify(data);
  return fetch(url, options).then(r => r.json());
}

function getFormData(formId) {
  const form = document.getElementById(formId);
  if (!form) return {};
  const fd = new FormData(form);
  return Object.fromEntries(fd.entries());
}

function reloadAfterDelay(ms = 800) {
  setTimeout(() => location.reload(), ms);
}


/* ============================================================
   CLIENTES CRUD
   ============================================================ */

function crearCliente() {
  const data = getFormData('form-crear-cliente');
  if (!data.nombre) return showToast('El nombre es requerido', 'error');
  apiRequest('/api/clientes', 'POST', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-crear-cliente'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function abrirEditarCliente(id, nombre, telefono, tipo, estado) {
  document.getElementById('edit-cliente-id').value = id;
  document.getElementById('edit-cliente-nombre').value = nombre;
  document.getElementById('edit-cliente-telefono').value = telefono;
  document.getElementById('edit-cliente-tipo').value = tipo;
  document.getElementById('edit-cliente-estado').value = estado;
  openModal('modal-editar-cliente');
}

function guardarEditarCliente() {
  const id = document.getElementById('edit-cliente-id').value;
  const data = {
    nombre: document.getElementById('edit-cliente-nombre').value,
    telefono: document.getElementById('edit-cliente-telefono').value,
    tipo_cliente: document.getElementById('edit-cliente-tipo').value,
    estado: document.getElementById('edit-cliente-estado').value,
  };
  apiRequest(`/api/clientes/${id}`, 'PUT', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-editar-cliente'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function eliminarCliente(id, nombre) {
  if (!confirm(`¿Eliminar al cliente "${nombre}"?`)) return;
  apiRequest(`/api/clientes/${id}`, 'DELETE').then(r => {
    if (r.success) { showToast(r.message); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function verCliente(id, nombre, telefono, tipo, estado, fecha) {
  document.getElementById('ver-cliente-nombre').textContent = nombre;
  document.getElementById('ver-cliente-telefono').textContent = telefono;
  document.getElementById('ver-cliente-tipo').textContent = tipo;
  document.getElementById('ver-cliente-estado').textContent = estado;
  document.getElementById('ver-cliente-fecha').textContent = fecha;
  document.getElementById('ver-cliente-id').textContent = id;
  openModal('modal-ver-cliente');
}

/* ============================================================
   VEHICULOS CRUD
   ============================================================ */

function crearVehiculo() {
  const data = getFormData('form-crear-vehiculo');
  if (!data.placa) return showToast('La placa es requerida', 'error');
  apiRequest('/api/vehiculos', 'POST', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-crear-vehiculo'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function abrirEditarVehiculo(id, placa, marca, modelo, color, clienteId) {
  document.getElementById('edit-vehiculo-id').value = id;
  document.getElementById('edit-vehiculo-placa').value = placa;
  document.getElementById('edit-vehiculo-marca').value = marca;
  document.getElementById('edit-vehiculo-modelo').value = modelo;
  document.getElementById('edit-vehiculo-color').value = color;
  document.getElementById('edit-vehiculo-cliente').value = clienteId;
  openModal('modal-editar-vehiculo');
}

function guardarEditarVehiculo() {
  const id = document.getElementById('edit-vehiculo-id').value;
  const data = {
    placa: document.getElementById('edit-vehiculo-placa').value,
    marca: document.getElementById('edit-vehiculo-marca').value,
    modelo: document.getElementById('edit-vehiculo-modelo').value,
    color: document.getElementById('edit-vehiculo-color').value,
    id_cliente: document.getElementById('edit-vehiculo-cliente').value,
  };
  apiRequest(`/api/vehiculos/${id}`, 'PUT', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-editar-vehiculo'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function eliminarVehiculo(id, placa) {
  if (!confirm(`¿Eliminar el vehículo con placa "${placa}"?`)) return;
  apiRequest(`/api/vehiculos/${id}`, 'DELETE').then(r => {
    if (r.success) { showToast(r.message); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

/* ============================================================
   ESTANCIAS (ENTRADA / SALIDA)
   ============================================================ */

function registrarEntrada() {
  const data = getFormData('form-entrada');
  if (!data.id_vehiculo) return showToast('Selecciona un vehículo', 'error');
  data.es_pension = data.es_pension === 'true';
  apiRequest('/api/estancias', 'POST', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-entrada'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function registrarSalida(idEstancia) {
  const metodo = document.getElementById(`metodo-pago-${idEstancia}`);
  const data = { metodo_pago: metodo ? metodo.value : 'EFECTIVO' };
  apiRequest(`/api/estancias/${idEstancia}/salida`, 'POST', data).then(r => {
    if (r.success) { showToast(r.message); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function confirmarSalida(idEstancia, placa) {
  document.getElementById('salida-id').value = idEstancia;
  document.getElementById('salida-placa').textContent = placa;
  openModal('modal-salida');
}

function procesarSalida() {
  const id = document.getElementById('salida-id').value;
  const metodo = document.getElementById('salida-metodo').value;
  const ref = document.getElementById('salida-referencia').value;
  apiRequest(`/api/estancias/${id}/salida`, 'POST', { metodo_pago: metodo, referencia: ref || null }).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-salida'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

/* ============================================================
   PENSIONES CRUD
   ============================================================ */

function crearPension() {
  const data = getFormData('form-crear-pension');
  if (!data.id_cliente) return showToast('Selecciona un cliente', 'error');
  apiRequest('/api/pensiones', 'POST', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-crear-pension'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function abrirEditarPension(id, clienteId, inicio, fin, costo, estado, obs) {
  document.getElementById('edit-pension-id').value = id;
  document.getElementById('edit-pension-cliente').value = clienteId;
  document.getElementById('edit-pension-inicio').value = inicio;
  document.getElementById('edit-pension-fin').value = fin;
  document.getElementById('edit-pension-costo').value = costo;
  document.getElementById('edit-pension-estado').value = estado;
  document.getElementById('edit-pension-obs').value = obs || '';
  openModal('modal-editar-pension');
}

function guardarEditarPension() {
  const id = document.getElementById('edit-pension-id').value;
  const data = {
    id_cliente: document.getElementById('edit-pension-cliente').value,
    fecha_inicio: document.getElementById('edit-pension-inicio').value,
    fecha_fin: document.getElementById('edit-pension-fin').value,
    costo_mensual: document.getElementById('edit-pension-costo').value,
    estado: document.getElementById('edit-pension-estado').value,
    observaciones: document.getElementById('edit-pension-obs').value || null,
  };
  apiRequest(`/api/pensiones/${id}`, 'PUT', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-editar-pension'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function cancelarPension(id) {
  if (!confirm('¿Cancelar esta pensión?')) return;
  apiRequest(`/api/pensiones/${id}`, 'DELETE').then(r => {
    if (r.success) { showToast(r.message); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

/* ============================================================
   TARIFAS
   ============================================================ */

function crearTarifa() {
  const data = getFormData('form-crear-tarifa');
  if (!data.descripcion) return showToast('La descripción es requerida', 'error');
  apiRequest('/api/tarifas', 'POST', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-crear-tarifa'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function abrirEditarTarifa(id, desc, tiempo, costo, costoExtra, estado) {
  document.getElementById('edit-tarifa-id').value = id;
  document.getElementById('edit-tarifa-desc').value = desc;
  document.getElementById('edit-tarifa-tiempo').value = tiempo;
  document.getElementById('edit-tarifa-costo').value = costo;
  document.getElementById('edit-tarifa-extra').value = costoExtra;
  document.getElementById('edit-tarifa-estado').value = estado;
  openModal('modal-editar-tarifa');
}

function guardarEditarTarifa() {
  const id = document.getElementById('edit-tarifa-id').value;
  const data = {
    descripcion: document.getElementById('edit-tarifa-desc').value,
    tiempo_inicial_min: document.getElementById('edit-tarifa-tiempo').value,
    costo_inicial: document.getElementById('edit-tarifa-costo').value,
    costo_por_min_extra: document.getElementById('edit-tarifa-extra').value,
    estado: document.getElementById('edit-tarifa-estado').value,
  };
  apiRequest(`/api/tarifas/${id}`, 'PUT', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-editar-tarifa'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

/* ============================================================
   USUARIOS CRUD
   ============================================================ */

function crearUsuario() {
  const data = getFormData('form-crear-usuario');
  if (!data.nombre || !data.username || !data.password) return showToast('Completa todos los campos', 'error');
  apiRequest('/api/usuarios', 'POST', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-crear-usuario'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function abrirEditarUsuario(id, nombre, email, username, perfil) {
  document.getElementById('edit-usuario-id').value = id;
  document.getElementById('edit-usuario-nombre').value = nombre;
  document.getElementById('edit-usuario-email').value = email;
  document.getElementById('edit-usuario-username').value = username;
  document.getElementById('edit-usuario-perfil').value = perfil;
  openModal('modal-editar-usuario');
}

function guardarEditarUsuario() {
  const id = document.getElementById('edit-usuario-id').value;
  const data = {
    nombre: document.getElementById('edit-usuario-nombre').value,
    email: document.getElementById('edit-usuario-email').value,
    username: document.getElementById('edit-usuario-username').value,
    perfil: document.getElementById('edit-usuario-perfil').value,
    password: document.getElementById('edit-usuario-password').value || null,
  };
  apiRequest(`/api/usuarios/${id}`, 'PUT', data).then(r => {
    if (r.success) { showToast(r.message); closeModal('modal-editar-usuario'); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function eliminarUsuario(id, nombre) {
  if (!confirm(`¿Eliminar al usuario "${nombre}"?`)) return;
  apiRequest(`/api/usuarios/${id}`, 'DELETE').then(r => {
    if (r.success) { showToast(r.message); reloadAfterDelay(); }
    else showToast(r.message, 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}
