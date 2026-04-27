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
      table.querySelectorAll('tr').forEach(row => {
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
   MÓDULO DE ESTANCIAS (ENTRADA / SALIDA / CARGA DINÁMICA)
   ============================================================ */

// Cargar estancias dinámicamente al abrir estancias.html
function cargarEstancias() {
  const tbodyActivas = document.getElementById('tbody-estancias-activas');
  const tbodyHistorial = document.getElementById('tbody-estancias-historial');
  const badgeActivos = document.getElementById('badge-activos');
  
  if (!tbodyActivas && !tbodyHistorial) return; // Solo ejecutar si estamos en la vista de estancias

  apiRequest('/api/estancias', 'GET')
    .then(data => {
      // Filtrar y limpiar tablas
      const activas = data.filter(e => e.estado === 'ACTIVO');
      const completadas = data.filter(e => e.estado === 'COMPLETADO');
      
      if(badgeActivos) badgeActivos.textContent = `(${activas.length})`;

      // Renderizar Activas
      if (tbodyActivas) {
        tbodyActivas.innerHTML = '';
        if (activas.length === 0) {
          tbodyActivas.innerHTML = '<tr><td colspan="5" style="text-align:center;">No hay vehículos actualmente</td></tr>';
        } else {
          activas.forEach(e => {
            tbodyActivas.innerHTML += `
              <tr>
                <td class="table-cell-mono">${e.id}</td>
                <td><span class="table-cell-mono" style="font-size:1rem;background:rgba(0,212,170,0.1);padding:4px 10px;border-radius:6px;">${e.matricula}</span></td>
                <td>${e.fecha_entrada} <br><small class="text-muted">${e.hora_entrada}</small></td>
                <td><span class="badge badge-info">${e.tipo}</span></td>
                <td>
                  <button class="btn btn-primary btn-sm" onclick="confirmarSalida(${e.id}, '${e.matricula}')">🏁 Salida</button>
                </td>
              </tr>
            `;
          });
        }
      }

      // Renderizar Historial
      if (tbodyHistorial) {
        tbodyHistorial.innerHTML = '';
        if (completadas.length === 0) {
          tbodyHistorial.innerHTML = '<tr><td colspan="6" style="text-align:center;">No hay registros en el historial</td></tr>';
        } else {
          completadas.forEach(e => {
            tbodyHistorial.innerHTML += `
              <tr>
                <td class="table-cell-mono">${e.id}</td>
                <td class="table-cell-mono">${e.matricula}</td>
                <td>${e.fecha_entrada} <br><small class="text-muted">${e.hora_entrada}</small></td>
                <td>${e.fecha_salida || '—'} <br><small class="text-muted">${e.hora_salida || ''}</small></td>
                <td><span class="badge badge-info">${e.tipo}</span></td>
                <td><span class="badge badge-purple">✅ Completada ($${e.total || '0.00'})</span></td>
              </tr>
            `;
          });
        }
      }
    })
    .catch(err => console.error("Error al cargar estancias:", err));
}

function registrarEntrada() {
  const data = getFormData('form-entrada');
  if (!data.matricula) return showToast('La matrícula es requerida', 'error');
  
  // Convertimos a mayúsculas por consistencia
  data.matricula = data.matricula.toUpperCase();

  apiRequest('/api/estancias', 'POST', data).then(r => {
    if (r.id || r.message) { 
      showToast('Entrada registrada correctamente'); 
      closeModal('modal-entrada'); 
      reloadAfterDelay(); 
    } else { 
      showToast(r.error || 'Error al registrar', 'error'); 
    }
  }).catch(() => showToast('Error de conexión', 'error'));
}

function confirmarSalida(idEstancia, matricula) {
  document.getElementById('salida-id').value = idEstancia;
  document.getElementById('salida-placa').textContent = matricula;
  openModal('modal-salida');
}

function procesarSalida() {
  const id = document.getElementById('salida-id').value;
  
  apiRequest(`/api/estancias/${id}/salida`, 'POST', {}).then(r => {
    if (r.message || r.total) { 
      // Si la API devuelve el total, lo mostramos
      const total = r.total !== undefined ? r.total : 'calculado';
      showToast(`Salida registrada. Total a cobrar: $${total}`); 
      closeModal('modal-salida'); 
      reloadAfterDelay(1500); // Damos un poco más de tiempo para que lean el total
    } else { 
      showToast(r.error || 'Error al procesar salida', 'error'); 
    }
  }).catch(() => showToast('Error de conexión', 'error'));
}

/* ============================================================
   CLIENTES CRUD
   ============================================================ */
function crearCliente() {
  const data = getFormData('form-crear-cliente');
  if (!data.nombre) return showToast('El nombre es requerido', 'error');
  apiRequest('/api/clientes', 'POST', data).then(r => {
    if (r.message && !r.error) { showToast(r.message); closeModal('modal-crear-cliente'); reloadAfterDelay(); }
    else showToast(r.error || 'Error al crear', 'error');
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
    if (r.message && !r.error) { showToast(r.message); closeModal('modal-editar-cliente'); reloadAfterDelay(); }
    else showToast(r.error || 'Error al actualizar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function eliminarCliente(id, nombre) {
  if (!confirm(`¿Eliminar al cliente "${nombre}"?`)) return;
  apiRequest(`/api/clientes/${id}`, 'DELETE').then(r => {
    if (r.message && !r.error) { showToast(r.message); reloadAfterDelay(); }
    else showToast(r.error || 'Error al eliminar', 'error');
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
   TARIFAS CRUD (Actualizado a BD MySQL nueva)
   ============================================================ */
function crearTarifa() {
  const data = getFormData('form-crear-tarifa');
  if (!data.tipo || !data.precio) return showToast('Tipo y precio son requeridos', 'error');
  apiRequest('/api/tarifas', 'POST', data).then(r => {
    if (r.message && !r.error) { showToast(r.message); closeModal('modal-crear-tarifa'); reloadAfterDelay(); }
    else showToast(r.error || 'Error al crear', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function abrirEditarTarifa(id, tipo, precio) {
  document.getElementById('edit-tarifa-id').value = id;
  document.getElementById('edit-tarifa-tipo').value = tipo;
  document.getElementById('edit-tarifa-precio').value = precio;
  openModal('modal-editar-tarifa');
}

function guardarEditarTarifa() {
  const id = document.getElementById('edit-tarifa-id').value;
  const data = {
    tipo: document.getElementById('edit-tarifa-tipo').value,
    precio: parseFloat(document.getElementById('edit-tarifa-precio').value),
  };
  apiRequest(`/api/tarifas/${id}`, 'PUT', data).then(r => {
    if (r.message && !r.error) { showToast(r.message); closeModal('modal-editar-tarifa'); reloadAfterDelay(); }
    else showToast(r.error || 'Error al actualizar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function eliminarTarifa(id, tipo) {
  if (!confirm(`¿Eliminar la tarifa "${tipo}"?`)) return;
  apiRequest(`/api/tarifas/${id}`, 'DELETE').then(r => {
    if (r.message && !r.error) { showToast(r.message); reloadAfterDelay(); }
    else showToast(r.error || 'Error al eliminar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

/* ============================================================
   USUARIOS CRUD
   ============================================================ */
function crearUsuario() {
  const data = getFormData('form-crear-usuario');
  if (!data.nombre || !data.username || !data.password) return showToast('Completa todos los campos', 'error');
  apiRequest('/api/usuarios', 'POST', data).then(r => {
    if (r.message && !r.error) { showToast(r.message); closeModal('modal-crear-usuario'); reloadAfterDelay(); }
    else showToast(r.error || 'Error al crear', 'error');
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
  };
  const pwd = document.getElementById('edit-usuario-password').value;
  if (pwd) data.password = pwd; // Solo envía password si se escribió algo

  apiRequest(`/api/usuarios/${id}`, 'PUT', data).then(r => {
    if (r.message && !r.error) { showToast(r.message); closeModal('modal-editar-usuario'); reloadAfterDelay(); }
    else showToast(r.error || 'Error al actualizar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function eliminarUsuario(id, nombre) {
  if (!confirm(`¿Eliminar al usuario "${nombre}"?`)) return;
  apiRequest(`/api/usuarios/${id}`, 'DELETE').then(r => {
    if (r.message && !r.error) { showToast(r.message); reloadAfterDelay(); }
    else showToast(r.error || 'Error al eliminar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function crearVehiculo(event) {
  if (event) event.preventDefault();
  const data = getFormData('form-crear-vehiculo');
  if (!data.matricula || !data.marca || !data.modelo || !data.color) return showToast('Llena los campos obligatorios', 'error');
  
  apiRequest('/api/vehiculos/crear', 'POST', data).then(r => {
    if (r.success || r.mensaje) { showToast(r.mensaje || 'Vehículo registrado correctamente'); closeModal('modal-crear-vehiculo'); reloadAfterDelay(); }
    else showToast(r.error || 'Error al crear', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function abrirEditarVehiculo(matricula, marca, modelo, color, cliente_id) {
  document.getElementById('edit-vehiculo-matricula').value = matricula;
  document.getElementById('edit-vehiculo-marca').value = marca;
  document.getElementById('edit-vehiculo-modelo').value = modelo;
  document.getElementById('edit-vehiculo-color').value = color;
  document.getElementById('edit-vehiculo-cliente').value = cliente_id || "";
  openModal('modal-editar-vehiculo');
}

function guardarEditarVehiculo() {
  const matricula = document.getElementById('edit-vehiculo-matricula').value;
  const data = {
    marca: document.getElementById('edit-vehiculo-marca').value,
    modelo: document.getElementById('edit-vehiculo-modelo').value,
    color: document.getElementById('edit-vehiculo-color').value,
    cliente_id: document.getElementById('edit-vehiculo-cliente').value,
  };
  apiRequest(`/api/vehiculos/${matricula}`, 'PUT', data).then(r => {
    if (r.success || r.message) { showToast(r.message || 'Vehículo actualizado'); closeModal('modal-editar-vehiculo'); reloadAfterDelay(); }
    else showToast(r.error || r.message || 'Error al actualizar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function eliminarVehiculo(matricula) {
  if (!confirm(`¿Eliminar el vehículo con matrícula "${matricula}"?`)) return;
  apiRequest(`/api/vehiculos/${matricula}`, 'DELETE').then(r => {
    if (r.success || r.message) { showToast(r.message || 'Vehículo eliminado'); reloadAfterDelay(); }
    else showToast(r.error || r.message || 'Error al eliminar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

/* ============================================================
   PENSIONES CRUD
   ============================================================ */
function crearPension() {
  const data = getFormData('form-crear-pension');
  if (!data.cliente_id || !data.matricula || !data.fecha_inicio || !data.fecha_fin || !data.monto) {
    return showToast('Completa todos los campos obligatorios', 'error');
  }
  apiRequest('/api/pensiones', 'POST', data).then(r => {
    if (r.success || r.message) { showToast(r.message || 'Pensión registrada'); closeModal('modal-crear-pension'); reloadAfterDelay(); }
    else showToast(r.error || r.message || 'Error al crear pensión', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function abrirEditarPension(id_pension, cliente_id, matricula, inicio, fin, monto, estatus) {
  document.getElementById('edit-pension-id').value = id_pension;
  document.getElementById('edit-pension-cliente').value = cliente_id || "";
  document.getElementById('edit-pension-matricula').value = matricula || "";
  document.getElementById('edit-pension-inicio').value = inicio;
  document.getElementById('edit-pension-fin').value = fin;
  document.getElementById('edit-pension-monto').value = monto;
  document.getElementById('edit-pension-estatus').value = estatus;
  openModal('modal-editar-pension');
}

function guardarEditarPension() {
  const id_pension = document.getElementById('edit-pension-id').value;
  const data = {
    cliente_id: document.getElementById('edit-pension-cliente').value,
    matricula: document.getElementById('edit-pension-matricula').value,
    fecha_inicio: document.getElementById('edit-pension-inicio').value,
    fecha_fin: document.getElementById('edit-pension-fin').value,
    monto: document.getElementById('edit-pension-monto').value,
    estatus: document.getElementById('edit-pension-estatus').value,
  };
  apiRequest(`/api/pensiones/${id_pension}`, 'PUT', data).then(r => {
    if (r.success || r.message) { showToast(r.message || 'Pensión actualizada'); closeModal('modal-editar-pension'); reloadAfterDelay(); }
    else showToast(r.error || r.message || 'Error al actualizar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}

function cancelarPension(id_pension) {
  if (!confirm('¿Seguro que deseas cancelar esta pensión?')) return;
  apiRequest(`/api/pensiones/${id_pension}`, 'DELETE').then(r => {
    if (r.success || r.message) { showToast(r.message || 'Pensión cancelada'); reloadAfterDelay(); }
    else showToast(r.error || r.message || 'Error al cancelar', 'error');
  }).catch(() => showToast('Error de conexión', 'error'));
}