from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from datetime import datetime, timedelta
import os, math

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ============================================================
# DATOS DE PRUEBA — Basados en el Diagrama ER
# ============================================================

# --- Usuarios (para login, no está en el ER pero se necesita) ---
usuarios_db = [
    {"id_usuario": 1, "nombre": "Admin Principal", "email": "admin@parking.com", "username": "admin", "password": "admin123", "perfil": "admin"},
    {"id_usuario": 2, "nombre": "Carlos López", "email": "carlos@parking.com", "username": "cobrador1", "password": "cobrador123", "perfil": "cobrador"},
    {"id_usuario": 3, "nombre": "María García", "email": "maria@parking.com", "username": "cobrador2", "password": "cobrador123", "perfil": "cobrador"},
]

# --- CLIENTE ---
clientes_db = [
    {"id_cliente": 1, "nombre": "Juan Pérez", "telefono": "6141234567", "tipo_cliente": "REGISTRADO", "fecha_registro": "2024-01-15 10:30:00", "estado": "ACTIVO"},
    {"id_cliente": 2, "nombre": "Ana Martínez", "telefono": "6149876543", "tipo_cliente": "REGISTRADO", "fecha_registro": "2025-06-01 14:00:00", "estado": "ACTIVO"},
    {"id_cliente": 3, "nombre": "Roberto Sánchez", "telefono": "6145551234", "tipo_cliente": "OCASIONAL", "fecha_registro": "2026-03-10 09:15:00", "estado": "ACTIVO"},
    {"id_cliente": 4, "nombre": "Laura Domínguez", "telefono": "6147778899", "tipo_cliente": "REGISTRADO", "fecha_registro": "2023-08-20 11:45:00", "estado": "ACTIVO"},
    {"id_cliente": 5, "nombre": "Pedro Ramírez", "telefono": "6142223344", "tipo_cliente": "OCASIONAL", "fecha_registro": "2026-04-01 16:20:00", "estado": "INACTIVO"},
]

# --- VEHICULO ---
vehiculos_db = [
    {"id_vehiculo": 1, "placa": "CHH-123-A", "marca": "Toyota", "modelo": "Corolla 2022", "color": "Blanco", "id_cliente": 1},
    {"id_vehiculo": 2, "placa": "CHH-456-B", "marca": "Honda", "modelo": "Civic 2021", "color": "Negro", "id_cliente": 2},
    {"id_vehiculo": 3, "placa": "CHH-789-C", "marca": "Nissan", "modelo": "Versa 2023", "color": "Rojo", "id_cliente": 3},
    {"id_vehiculo": 4, "placa": "CHH-012-D", "marca": "Ford", "modelo": "Focus 2020", "color": "Azul", "id_cliente": 1},
    {"id_vehiculo": 5, "placa": "CHH-345-E", "marca": "Chevrolet", "modelo": "Aveo 2024", "color": "Gris", "id_cliente": 4},
    {"id_vehiculo": 6, "placa": "CHH-678-F", "marca": "Volkswagen", "modelo": "Jetta 2022", "color": "Blanco", "id_cliente": 5},
]

# --- TARIFA ---
tarifas_db = [
    {"id_tarifa": 1, "descripcion": "Tarifa Estándar", "tiempo_inicial_min": 60, "costo_inicial": 20.00, "costo_por_min_extra": 0.25, "estado": "ACTIVA", "fecha_creacion": "2026-01-01 00:00:00"},
    {"id_tarifa": 2, "descripcion": "Tarifa Nocturna", "tiempo_inicial_min": 120, "costo_inicial": 15.00, "costo_por_min_extra": 0.15, "estado": "ACTIVA", "fecha_creacion": "2026-01-01 00:00:00"},
    {"id_tarifa": 3, "descripcion": "Tarifa Fin de Semana", "tiempo_inicial_min": 90, "costo_inicial": 25.00, "costo_por_min_extra": 0.30, "estado": "ACTIVA", "fecha_creacion": "2026-02-15 00:00:00"},
    {"id_tarifa": 4, "descripcion": "Tarifa Especial Eventos", "tiempo_inicial_min": 60, "costo_inicial": 35.00, "costo_por_min_extra": 0.40, "estado": "INACTIVA", "fecha_creacion": "2026-03-01 00:00:00"},
]

# --- ESTANCIA ---
estancias_db = [
    {"id_estancia": 1, "id_vehiculo": 1, "fecha_entrada": "2026-04-23 08:30:00", "fecha_salida": None, "id_tarifa": 1, "es_pension": False},
    {"id_estancia": 2, "id_vehiculo": 2, "fecha_entrada": "2026-04-23 09:15:00", "fecha_salida": None, "id_tarifa": 1, "es_pension": False},
    {"id_estancia": 3, "id_vehiculo": 3, "fecha_entrada": "2026-04-22 10:00:00", "fecha_salida": "2026-04-22 11:30:00", "id_tarifa": 1, "es_pension": False},
    {"id_estancia": 4, "id_vehiculo": 5, "fecha_entrada": "2026-04-23 07:45:00", "fecha_salida": None, "id_tarifa": 1, "es_pension": True},
    {"id_estancia": 5, "id_vehiculo": 4, "fecha_entrada": "2026-04-21 14:00:00", "fecha_salida": "2026-04-21 16:15:00", "id_tarifa": 2, "es_pension": False},
]

# --- PENSION ---
pensiones_db = [
    {"id_pension": 1, "id_cliente": 1, "fecha_inicio": "2024-01-15", "fecha_fin": "2026-01-15", "costo_mensual": 2500.00, "estado": "ACTIVA", "observaciones": "Cliente frecuente desde 2024"},
    {"id_pension": 2, "id_cliente": 4, "fecha_inicio": "2025-06-01", "fecha_fin": "2026-06-01", "costo_mensual": 2500.00, "estado": "ACTIVA", "observaciones": None},
    {"id_pension": 3, "id_cliente": 2, "fecha_inicio": "2025-01-01", "fecha_fin": "2025-12-31", "costo_mensual": 2200.00, "estado": "CANCELADA", "observaciones": "Cancelada por cambio de domicilio"},
]

# --- PAGO ---
pagos_db = [
    {"id_pago": 1, "id_estancia": 3, "id_pension": None, "monto": 27.50, "fecha_pago": "2026-04-22 11:30:00", "metodo_pago": "EFECTIVO", "referencia": None, "observaciones": None},
    {"id_pago": 2, "id_estancia": 5, "id_pension": None, "monto": 33.75, "fecha_pago": "2026-04-21 16:15:00", "metodo_pago": "TARJETA", "referencia": "TXN-00452", "observaciones": None},
    {"id_pago": 3, "id_estancia": None, "id_pension": 1, "monto": 2500.00, "fecha_pago": "2026-04-01 10:00:00", "metodo_pago": "TRANSFERENCIA", "referencia": "SPEI-789456", "observaciones": "Pago pensión abril 2026"},
    {"id_pago": 4, "id_estancia": None, "id_pension": 2, "monto": 2500.00, "fecha_pago": "2026-04-01 11:00:00", "metodo_pago": "EFECTIVO", "referencia": None, "observaciones": "Pago pensión abril 2026"},
]

# ID counters
next_ids = {
    "cliente": 6, "vehiculo": 7, "estancia": 6, "tarifa": 5, "pension": 4, "pago": 5, "usuario": 4
}


# ============================================================
# HELPERS
# ============================================================

def get_cliente(id_cliente):
    return next((c for c in clientes_db if c['id_cliente'] == id_cliente), None)

def get_vehiculo(id_vehiculo):
    return next((v for v in vehiculos_db if v['id_vehiculo'] == id_vehiculo), None)

def get_vehiculo_by_placa(placa):
    return next((v for v in vehiculos_db if v['placa'] == placa), None)

def get_tarifa(id_tarifa):
    return next((t for t in tarifas_db if t['id_tarifa'] == id_tarifa), None)

def get_pension(id_pension):
    return next((p for p in pensiones_db if p['id_pension'] == id_pension), None)

def calcular_monto(estancia):
    """Calcula el monto según la tarifa: costo_inicial por tiempo_inicial_min, luego costo_por_min_extra."""
    tarifa = get_tarifa(estancia['id_tarifa'])
    if not tarifa:
        return 0
    entrada = datetime.strptime(estancia['fecha_entrada'], "%Y-%m-%d %H:%M:%S")
    if estancia['fecha_salida']:
        salida = datetime.strptime(estancia['fecha_salida'], "%Y-%m-%d %H:%M:%S")
    else:
        salida = datetime.now()
    minutos = max(1, int((salida - entrada).total_seconds() / 60))
    if minutos <= tarifa['tiempo_inicial_min']:
        return tarifa['costo_inicial']
    else:
        extra = minutos - tarifa['tiempo_inicial_min']
        return round(tarifa['costo_inicial'] + extra * tarifa['costo_por_min_extra'], 2)

def calcular_estancia_str(estancia):
    """Returns a human-readable duration string."""
    entrada = datetime.strptime(estancia['fecha_entrada'], "%Y-%m-%d %H:%M:%S")
    if estancia['fecha_salida']:
        salida = datetime.strptime(estancia['fecha_salida'], "%Y-%m-%d %H:%M:%S")
    else:
        salida = datetime.now()
    delta = salida - entrada
    hours = int(delta.total_seconds() // 3600)
    mins = int((delta.total_seconds() % 3600) // 60)
    return f"{hours}h {mins}m"


# ============================================================
# AUTH DECORATORS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session['user']['perfil'] != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# TEMPLATE CONTEXT
# ============================================================

@app.context_processor
def inject_helpers():
    def _get_cliente(id_c):
        return get_cliente(id_c)
    def _get_vehiculo(id_v):
        return get_vehiculo(id_v)
    def _get_tarifa(id_t):
        return get_tarifa(id_t)
    def _calcular_monto(est):
        return calcular_monto(est)
    def _calcular_estancia(est):
        return calcular_estancia_str(est)
    active_count = len([e for e in estancias_db if not e['fecha_salida']])
    return dict(
        get_cliente=_get_cliente,
        get_vehiculo=_get_vehiculo,
        get_tarifa=_get_tarifa,
        calcular_monto=_calcular_monto,
        calcular_estancia=_calcular_estancia,
        vehiculos_activos_count=active_count,
    )


# ============================================================
# PAGE ROUTES
# ============================================================

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = next((u for u in usuarios_db if u['username'] == username and u['password'] == password), None)
        if user:
            session['user'] = user
            flash('Bienvenido, ' + user['nombre'], 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    estancias_activas = [e for e in estancias_db if not e['fecha_salida']]
    total_ingresos_hoy = sum(p['monto'] for p in pagos_db if p['fecha_pago'].startswith('2026-04-23'))
    total_ingresos_mes = sum(p['monto'] for p in pagos_db if p['fecha_pago'].startswith('2026-04'))
    stats = {
        "vehiculos_dentro": len(estancias_activas),
        "total_clientes": len([c for c in clientes_db if c['estado'] == 'ACTIVO']),
        "pensiones_activas": len([p for p in pensiones_db if p['estado'] == 'ACTIVA']),
        "ingresos_hoy": total_ingresos_hoy,
        "ingresos_mes": total_ingresos_mes,
    }
    return render_template('dashboard.html', stats=stats, estancias_activas=estancias_activas, tarifas=tarifas_db)


@app.route('/clientes')
@login_required
def clientes():
    return render_template('clientes.html', clientes=clientes_db)


@app.route('/vehiculos')
@login_required
def vehiculos():
    return render_template('vehiculos.html', vehiculos=vehiculos_db, clientes=clientes_db)


@app.route('/estancias')
@login_required
def estancias():
    return render_template('estancias.html', estancias=estancias_db, vehiculos=vehiculos_db, tarifas=[t for t in tarifas_db if t['estado'] == 'ACTIVA'])


@app.route('/pagos')
@login_required
def pagos():
    return render_template('pagos.html', pagos=pagos_db, estancias=estancias_db)


@app.route('/pensiones')
@login_required
def pensiones():
    return render_template('pensiones.html', pensiones=pensiones_db, clientes=clientes_db, vehiculos=vehiculos_db)


@app.route('/tarifas')
@login_required
def tarifas():
    return render_template('tarifas.html', tarifas=tarifas_db)


@app.route('/usuarios')
@admin_required
def usuarios():
    return render_template('usuarios.html', usuarios=usuarios_db)


@app.route('/reportes')
@admin_required
def reportes():
    return render_template('reportes.html')


# ============================================================
# CRUD API — CLIENTES
# ============================================================

@app.route('/api/clientes', methods=['POST'])
@login_required
def api_crear_cliente():
    data = request.json
    nuevo = {
        "id_cliente": next_ids["cliente"],
        "nombre": data.get("nombre", ""),
        "telefono": data.get("telefono", ""),
        "tipo_cliente": data.get("tipo_cliente", "OCASIONAL"),
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estado": "ACTIVO",
    }
    next_ids["cliente"] += 1
    clientes_db.append(nuevo)
    return jsonify({"success": True, "message": "Cliente registrado correctamente", "data": nuevo})


@app.route('/api/clientes/<int:id_cliente>', methods=['PUT'])
@login_required
def api_editar_cliente(id_cliente):
    data = request.json
    cliente = get_cliente(id_cliente)
    if not cliente:
        return jsonify({"success": False, "message": "Cliente no encontrado"})
    cliente['nombre'] = data.get('nombre', cliente['nombre'])
    cliente['telefono'] = data.get('telefono', cliente['telefono'])
    cliente['tipo_cliente'] = data.get('tipo_cliente', cliente['tipo_cliente'])
    cliente['estado'] = data.get('estado', cliente['estado'])
    return jsonify({"success": True, "message": "Cliente actualizado correctamente"})


@app.route('/api/clientes/<int:id_cliente>', methods=['DELETE'])
@login_required
def api_eliminar_cliente(id_cliente):
    global clientes_db
    clientes_db = [c for c in clientes_db if c['id_cliente'] != id_cliente]
    return jsonify({"success": True, "message": "Cliente eliminado correctamente"})


# ============================================================
# CRUD API — VEHICULOS
# ============================================================

@app.route('/api/vehiculos', methods=['POST'])
@login_required
def api_crear_vehiculo():
    data = request.json
    nuevo = {
        "id_vehiculo": next_ids["vehiculo"],
        "placa": data.get("placa", "").upper(),
        "marca": data.get("marca", ""),
        "modelo": data.get("modelo", ""),
        "color": data.get("color", ""),
        "id_cliente": int(data.get("id_cliente", 0)),
    }
    next_ids["vehiculo"] += 1
    vehiculos_db.append(nuevo)
    return jsonify({"success": True, "message": "Vehículo registrado correctamente", "data": nuevo})


@app.route('/api/vehiculos/<int:id_vehiculo>', methods=['PUT'])
@login_required
def api_editar_vehiculo(id_vehiculo):
    data = request.json
    v = get_vehiculo(id_vehiculo)
    if not v:
        return jsonify({"success": False, "message": "Vehículo no encontrado"})
    v['placa'] = data.get('placa', v['placa']).upper()
    v['marca'] = data.get('marca', v['marca'])
    v['modelo'] = data.get('modelo', v['modelo'])
    v['color'] = data.get('color', v['color'])
    v['id_cliente'] = int(data.get('id_cliente', v['id_cliente']))
    return jsonify({"success": True, "message": "Vehículo actualizado correctamente"})


@app.route('/api/vehiculos/<int:id_vehiculo>', methods=['DELETE'])
@login_required
def api_eliminar_vehiculo(id_vehiculo):
    global vehiculos_db
    vehiculos_db = [v for v in vehiculos_db if v['id_vehiculo'] != id_vehiculo]
    return jsonify({"success": True, "message": "Vehículo eliminado correctamente"})


# ============================================================
# CRUD API — ESTANCIAS
# ============================================================

@app.route('/api/estancias', methods=['POST'])
@login_required
def api_crear_estancia():
    data = request.json
    nueva = {
        "id_estancia": next_ids["estancia"],
        "id_vehiculo": int(data.get("id_vehiculo", 0)),
        "fecha_entrada": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_salida": None,
        "id_tarifa": int(data.get("id_tarifa", 1)),
        "es_pension": data.get("es_pension", False),
    }
    next_ids["estancia"] += 1
    estancias_db.append(nueva)
    vehiculo = get_vehiculo(nueva['id_vehiculo'])
    placa = vehiculo['placa'] if vehiculo else 'N/A'
    return jsonify({"success": True, "message": f"Entrada registrada — Placa: {placa}", "data": nueva})


@app.route('/api/estancias/<int:id_estancia>/salida', methods=['POST'])
@login_required
def api_registrar_salida(id_estancia):
    estancia = next((e for e in estancias_db if e['id_estancia'] == id_estancia), None)
    if not estancia:
        return jsonify({"success": False, "message": "Estancia no encontrada"})
    if estancia['fecha_salida']:
        return jsonify({"success": False, "message": "La estancia ya tiene salida registrada"})

    estancia['fecha_salida'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    monto = calcular_monto(estancia)

    # Create payment automatically
    data = request.json or {}
    pago = {
        "id_pago": next_ids["pago"],
        "id_estancia": id_estancia,
        "id_pension": None,
        "monto": monto,
        "fecha_pago": estancia['fecha_salida'],
        "metodo_pago": data.get("metodo_pago", "EFECTIVO"),
        "referencia": data.get("referencia", None),
        "observaciones": None,
    }
    next_ids["pago"] += 1
    pagos_db.append(pago)

    duracion = calcular_estancia_str(estancia)
    return jsonify({"success": True, "message": f"Salida registrada — Duración: {duracion} — Total: ${monto:.2f}", "data": {"estancia": estancia, "pago": pago}})


# ============================================================
# CRUD API — PENSIONES
# ============================================================

@app.route('/api/pensiones', methods=['POST'])
@login_required
def api_crear_pension():
    data = request.json
    nueva = {
        "id_pension": next_ids["pension"],
        "id_cliente": int(data.get("id_cliente", 0)),
        "fecha_inicio": data.get("fecha_inicio", ""),
        "fecha_fin": data.get("fecha_fin", ""),
        "costo_mensual": float(data.get("costo_mensual", 2500.00)),
        "estado": "ACTIVA",
        "observaciones": data.get("observaciones", None) or None,
    }
    next_ids["pension"] += 1
    pensiones_db.append(nueva)
    return jsonify({"success": True, "message": "Pensión registrada correctamente", "data": nueva})


@app.route('/api/pensiones/<int:id_pension>', methods=['PUT'])
@login_required
def api_editar_pension(id_pension):
    data = request.json
    pension = get_pension(id_pension)
    if not pension:
        return jsonify({"success": False, "message": "Pensión no encontrada"})
    pension['fecha_inicio'] = data.get('fecha_inicio', pension['fecha_inicio'])
    pension['fecha_fin'] = data.get('fecha_fin', pension['fecha_fin'])
    pension['costo_mensual'] = float(data.get('costo_mensual', pension['costo_mensual']))
    pension['estado'] = data.get('estado', pension['estado'])
    pension['observaciones'] = data.get('observaciones', pension['observaciones'])
    return jsonify({"success": True, "message": "Pensión actualizada correctamente"})


@app.route('/api/pensiones/<int:id_pension>', methods=['DELETE'])
@login_required
def api_eliminar_pension(id_pension):
    pension = get_pension(id_pension)
    if pension:
        pension['estado'] = 'CANCELADA'
    return jsonify({"success": True, "message": "Pensión cancelada correctamente"})


# ============================================================
# CRUD API — TARIFAS
# ============================================================

@app.route('/api/tarifas', methods=['POST'])
@login_required
def api_crear_tarifa():
    data = request.json
    nueva = {
        "id_tarifa": next_ids["tarifa"],
        "descripcion": data.get("descripcion", ""),
        "tiempo_inicial_min": int(data.get("tiempo_inicial_min", 60)),
        "costo_inicial": float(data.get("costo_inicial", 20.00)),
        "costo_por_min_extra": float(data.get("costo_por_min_extra", 0.25)),
        "estado": "ACTIVA",
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    next_ids["tarifa"] += 1
    tarifas_db.append(nueva)
    return jsonify({"success": True, "message": "Tarifa creada correctamente", "data": nueva})


@app.route('/api/tarifas/<int:id_tarifa>', methods=['PUT'])
@login_required
def api_editar_tarifa(id_tarifa):
    data = request.json
    tarifa = get_tarifa(id_tarifa)
    if not tarifa:
        return jsonify({"success": False, "message": "Tarifa no encontrada"})
    tarifa['descripcion'] = data.get('descripcion', tarifa['descripcion'])
    tarifa['tiempo_inicial_min'] = int(data.get('tiempo_inicial_min', tarifa['tiempo_inicial_min']))
    tarifa['costo_inicial'] = float(data.get('costo_inicial', tarifa['costo_inicial']))
    tarifa['costo_por_min_extra'] = float(data.get('costo_por_min_extra', tarifa['costo_por_min_extra']))
    tarifa['estado'] = data.get('estado', tarifa['estado'])
    return jsonify({"success": True, "message": "Tarifa actualizada correctamente"})


# ============================================================
# CRUD API — USUARIOS
# ============================================================

@app.route('/api/usuarios', methods=['POST'])
@admin_required
def api_crear_usuario():
    data = request.json
    nuevo = {
        "id_usuario": next_ids["usuario"],
        "nombre": data.get("nombre", ""),
        "email": data.get("email", ""),
        "username": data.get("username", ""),
        "password": data.get("password", ""),
        "perfil": data.get("perfil", "cobrador"),
    }
    next_ids["usuario"] += 1
    usuarios_db.append(nuevo)
    return jsonify({"success": True, "message": "Usuario creado correctamente", "data": nuevo})


@app.route('/api/usuarios/<int:id_usuario>', methods=['PUT'])
@admin_required
def api_editar_usuario(id_usuario):
    data = request.json
    user = next((u for u in usuarios_db if u['id_usuario'] == id_usuario), None)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"})
    user['nombre'] = data.get('nombre', user['nombre'])
    user['email'] = data.get('email', user['email'])
    user['username'] = data.get('username', user['username'])
    if data.get('password'):
        user['password'] = data['password']
    user['perfil'] = data.get('perfil', user['perfil'])
    return jsonify({"success": True, "message": "Usuario actualizado correctamente"})


@app.route('/api/usuarios/<int:id_usuario>', methods=['DELETE'])
@admin_required
def api_eliminar_usuario(id_usuario):
    global usuarios_db
    if id_usuario == session.get('user', {}).get('id_usuario'):
        return jsonify({"success": False, "message": "No puedes eliminar tu propio usuario"})
    usuarios_db = [u for u in usuarios_db if u['id_usuario'] != id_usuario]
    return jsonify({"success": True, "message": "Usuario eliminado correctamente"})


# ============================================================
# STATS API
# ============================================================

@app.route('/api/stats')
@login_required
def api_stats():
    return jsonify({
        "vehiculos_dentro": len([e for e in estancias_db if not e['fecha_salida']]),
        "total_clientes": len([c for c in clientes_db if c['estado'] == 'ACTIVO']),
        "pensiones_activas": len([p for p in pensiones_db if p['estado'] == 'ACTIVA']),
    })


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
