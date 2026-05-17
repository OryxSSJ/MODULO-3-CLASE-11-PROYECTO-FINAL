
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
from functools import wraps
import mysql.connector
from datetime import datetime, timedelta
import os, math
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'parksystem-fallback-key-2024')

# Monto base de pension mensual (configurable desde .env)
PENSION_MENSUAL_BASE = float(os.getenv('PENSION_MENSUAL_BASE', 1500))

# ============================================================
# Configuracion de la db (desde variables de entorno)
# ============================================================
DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'estacionamiento_db')
}

# ============================================================
# AUTH DECORATORS
# ============================================================
def get_db_connection():
    if 'db' not in g or not g.db.is_connected():
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db

def get_db():
    return get_db_connection()

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except:
            pass

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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True) 
            query = "SELECT * FROM USUARIO WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user['password'], password):
                session['user'] = user
                flash('Bienvenido, '+ user['nombre'], 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuario o contraseña incorrectos', 'error')
        except mysql.connector.Error as err:
            flash(f'Error de conexion a la base de datos: {err}', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.context_processor
def inject_global_stats():
    if 'user' not in session:
        return dict(global_stats=None)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as vehiculos_dentro FROM ESTANCIA WHERE fecha_salida IS NULL")
        vehiculos_dentro = cursor.fetchone()['vehiculos_dentro']
        cursor.execute("SELECT COUNT(*) as total_clientes FROM CLIENTE")
        total_clientes = cursor.fetchone()['total_clientes']
        cursor.execute("SELECT SUM(monto) as ingresos_hoy FROM PAGO WHERE DATE(fecha_pago) = CURDATE()")
        r = cursor.fetchone()
        ingresos_hoy = r['ingresos_hoy'] if r and r['ingresos_hoy'] else 0
        cursor.execute("SELECT COUNT(*) as pensiones_activas FROM PENSION WHERE estado='ACTIVA'")
        pensiones_activas = cursor.fetchone()['pensiones_activas']
        return dict(global_stats={
            'vehiculos_dentro': vehiculos_dentro,
            'total_clientes': total_clientes,
            'ingresos_hoy': float(ingresos_hoy),
            'pensiones_activas': pensiones_activas
        })
    except Exception as e:
        return dict(global_stats=None)

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("""
        SELECT e.id_estancia as folio_servicio, v.placa as matricula,
               DATE(e.fecha_entrada) as fecha_entrada, TIME(e.fecha_entrada) as hora_entrada,
               t.descripcion as tipo
        FROM ESTANCIA e
        JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo
        LEFT JOIN TARIFA t ON e.id_tarifa = t.id_tarifa
        WHERE e.fecha_salida IS NULL
        """)
        estancias_activas = cursor.fetchall()
        ingresos_hoy = float(g.global_stats['ingresos_hoy']) if g.get('global_stats') else 0
        return render_template('dashboard.html',
            stats={'ingresos_hoy': ingresos_hoy},
            estancias_activas=estancias_activas)
    except mysql.connector.Error as err:
        flash(f'Error de DB: {err}', 'error')
        return render_template('dashboard.html', estancias_activas=[])

@app.route('/clientes')
@login_required
def clientes():
    try:
      conn = get_db()
      cursor = conn.cursor(dictionary=True)
      cursor.execute("SELECT id_cliente as cliente_id, nombre, telefono, LOWER(tipo_cliente) as tipo, fecha_registro, LOWER(estado) as estado FROM CLIENTE")
      lista_clientes = cursor.fetchall()
      return render_template('clientes.html', clientes=lista_clientes)
    except mysql.connector.Error as err:
        flash(f'Error al cargar clientes: {err}', 'error')
    return render_template('clientes.html', clientes=[])

@app.route('/vehiculos')
@login_required
def vehiculos():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.id_vehiculo as matricula_id, v.placa as matricula, v.marca, v.modelo, v.color, LOWER(v.estado) as estado, v.id_cliente as cliente_id, c.nombre as nombre_cliente 
            FROM VEHICULO v 
            LEFT JOIN CLIENTE c ON v.id_cliente = c.id_cliente
        """)
        lista_vehiculos = cursor.fetchall()
        
        cursor.execute("SELECT id_cliente as cliente_id, nombre, LOWER(estado) as estado FROM CLIENTE")
        lista_clientes = cursor.fetchall()
        
        return render_template('vehiculos.html', vehiculos=lista_vehiculos, clientes=lista_clientes)
    except mysql.connector.Error as err:
        flash(f'Error al cargar vehículos: {err}', 'error')
        return render_template('vehiculos.html', vehiculos=[], clientes=[])

@app.route('/estancias')
@login_required
def estancias():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.id_estancia as folio_servicio, v.placa as matricula, 
                   DATE(e.fecha_entrada) as fecha_entrada, TIME(e.fecha_entrada) as hora_entrada, 
                   DATE(e.fecha_salida) as fecha_salida, TIME(e.fecha_salida) as hora_salida,
                   t.costo_hora as precio, t.descripcion as nombre_tarifa 
            FROM ESTANCIA e
            JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo
            LEFT JOIN TARIFA t ON e.id_tarifa = t.id_tarifa
            ORDER BY e.fecha_salida ASC, e.fecha_entrada DESC
        """)
        lista_estancias = cursor.fetchall()
        
        cursor.execute("SELECT placa as matricula FROM VEHICULO")
        lista_vehiculos = cursor.fetchall()
        
        cursor.execute("SELECT id_tarifa as folio_precio, descripcion as tipo, costo_hora as precio FROM TARIFA WHERE estado = 'ACTIVA'")
        lista_tarifas = cursor.fetchall()
        
        return render_template('estancias.html', estancias=lista_estancias, vehiculos=lista_vehiculos, tarifas=lista_tarifas)
    except mysql.connector.Error as err:
        flash(f'Error al cargar estancias: {err}', 'error')
        return render_template('estancias.html', estancias=[], vehiculos=[], tarifas=[])

@app.route('/pagos')
@login_required
def pagos():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*, v.placa as placa_vehiculo, t.descripcion as tarifa_desc
            FROM PAGO p 
            LEFT JOIN ESTANCIA e ON p.id_estancia = e.id_estancia 
            LEFT JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo 
            LEFT JOIN TARIFA t ON e.id_tarifa = t.id_tarifa
            ORDER BY p.fecha_pago DESC
        """)
        lista_cobros = cursor.fetchall()
        return render_template('pagos.html', pagos=lista_cobros)
    except mysql.connector.Error as err:
        flash(f'Error al cargar cobros: {err}', 'error')
        return render_template('pagos.html', pagos=[])

@app.route('/pensiones')
@login_required
def pensiones():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id_pension as pension_id, p.id_cliente as cliente_id, p.id_vehiculo, p.fecha_inicio, p.fecha_fin, p.costo_mensual as monto, p.estado as estatus, c.nombre as nombre_cliente, v.placa
            FROM PENSION p
            LEFT JOIN CLIENTE c ON p.id_cliente = c.id_cliente
            LEFT JOIN VEHICULO v ON p.id_vehiculo = v.id_vehiculo
        """)
        lista_pensiones = cursor.fetchall()
        
        # Calcular ingresos mensuales activos (robusto desde Python)
        ingreso_mensual_pensiones = sum(float(p['monto'] or 0) for p in lista_pensiones if p['estatus'] == 'ACTIVA')
        
        cursor.execute("SELECT id_cliente as cliente_id, nombre, LOWER(estado) as estado FROM CLIENTE")
        lista_clientes = cursor.fetchall()
        
        cursor.execute("SELECT v.id_vehiculo, v.placa, v.id_cliente, c.nombre as nombre_cliente FROM VEHICULO v LEFT JOIN CLIENTE c ON v.id_cliente = c.id_cliente")
        lista_vehiculos = cursor.fetchall()
        
        return render_template('pensiones.html', pensiones=lista_pensiones, clientes=lista_clientes, vehiculos=lista_vehiculos,
                               ingreso_mensual=ingreso_mensual_pensiones, pension_base=PENSION_MENSUAL_BASE)
    except mysql.connector.Error as err:
        flash(f'Error al cargar pensiones: {err}', 'error')
        return render_template('pensiones.html', pensiones=[], clientes=[])

@app.route('/tarifas')
@login_required
def tarifas():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM TARIFA")
        lista_precios = cursor.fetchall()
        return render_template('tarifas.html', tarifas=lista_precios)
    except mysql.connector.Error as err:
        flash(f'Error al cargar tarifas: {err}', 'error')
        return render_template('tarifas.html', tarifas=[])

@app.route('/usuarios')
@admin_required
def usuarios():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_usuario as usuario_id, nombre, email, username, perfil FROM USUARIO")
        lista_usuarios = cursor.fetchall()
        return render_template('usuarios.html', usuarios=lista_usuarios)
    except mysql.connector.Error as err:
        flash(f'Error al cargar usuarios: {err}', 'error')
        return render_template('usuarios.html', usuarios=[])

@app.route('/reportes')
@admin_required
def reportes():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT MONTH(fecha_entrada) as mes, COUNT(*) as entradas,
                   SUM(CASE WHEN fecha_salida IS NOT NULL THEN 1 ELSE 0 END) as salidas
            FROM ESTANCIA
            WHERE YEAR(fecha_entrada) = YEAR(CURDATE())
            GROUP BY MONTH(fecha_entrada)
        """)
        es_por_mes = cursor.fetchall()

        cursor.execute("""
            SELECT MONTH(fecha_entrada) as mes, COUNT(*) as total_servicios
            FROM ESTANCIA
            WHERE YEAR(fecha_entrada) = YEAR(CURDATE())
            GROUP BY MONTH(fecha_entrada)
            ORDER BY total_servicios DESC
            LIMIT 3
        """)
        meses_demanda = cursor.fetchall()

        cursor.execute("""
            SELECT HOUR(fecha_entrada) as hora, COUNT(*) as cantidad
            FROM ESTANCIA
            WHERE YEAR(fecha_entrada) = YEAR(CURDATE())
            GROUP BY HOUR(fecha_entrada)
            ORDER BY cantidad DESC
        """)
        horas_demanda = cursor.fetchall()

        cursor.execute("""
            SELECT MONTH(fecha_pago) as mes,
                   SUM(CASE WHEN id_estancia IS NOT NULL THEN monto ELSE 0 END) as ingresos_cajon,
                   SUM(CASE WHEN id_pension  IS NOT NULL THEN monto ELSE 0 END) as ingresos_pension
            FROM PAGO
            WHERE YEAR(fecha_pago) = YEAR(CURDATE())
            GROUP BY MONTH(fecha_pago)
        """)
        ingresos_mes = cursor.fetchall()

        # Pre-calcular alturas en px (180px = 100%) para Jinja2
        meses_str = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
        max_es   = max((max(int(d['entradas']), int(d['salidas'])) for d in es_por_mes), default=1) or 1
        max_hora = max((int(d['cantidad']) for d in horas_demanda), default=1) or 1
        max_ing  = max((float(d['ingresos_cajon'] or 0)+float(d['ingresos_pension'] or 0) for d in ingresos_mes), default=1) or 1

        for d in es_por_mes:
            d['mes_str']  = meses_str[int(d['mes'])-1]
            d['h_e'] = round(int(d['entradas']) / max_es * 180)
            d['h_s'] = round(int(d['salidas'])  / max_es * 180)
        for d in horas_demanda:
            d['h_bar'] = round(int(d['cantidad']) / max_hora * 180)
        for d in ingresos_mes:
            d['mes_str'] = meses_str[int(d['mes'])-1]
            total = float(d['ingresos_cajon'] or 0) + float(d['ingresos_pension'] or 0)
            d['total'] = total
            d['h_bar'] = round(total / max_ing * 180)
        for d in meses_demanda:
            d['mes_str'] = meses_str[int(d['mes'])-1]

        total_cajon   = sum(float(d['ingresos_cajon']   or 0) for d in ingresos_mes)
        total_pension = sum(float(d['ingresos_pension'] or 0) for d in ingresos_mes)

        return render_template('reportes.html',
            es_por_mes=es_por_mes, meses_demanda=meses_demanda,
            horas_demanda=horas_demanda, ingresos_mes=ingresos_mes,
            total_cajon=total_cajon, total_pension=total_pension,
            total_ingresos=total_cajon+total_pension)
    except Exception as err:
        flash(f'Error al cargar reportes: {err}', 'error')
        return render_template('reportes.html',
            es_por_mes=[], meses_demanda=[], horas_demanda=[],
            ingresos_mes=[], total_cajon=0, total_pension=0, total_ingresos=0)


# ============================================================
# CRUD API — CLIENTES
# ============================================================
@app.route('/api/clientes', methods=['POST'])
@login_required
def api_crear_cliente():
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        tipo = data.get("tipo") or data.get("tipo_cliente") or "OCASIONAL"
        query = "INSERT INTO CLIENTE (nombre, telefono, tipo_cliente) VALUES (%s, %s, %s)"
        valores = (data.get("nombre", ""), data.get("telefono", ""), tipo.upper())
        cursor.execute(query, valores)
        conn.commit()
        nuevo_id = cursor.lastrowid
        return jsonify({"success": True, "message": "Cliente registrado", "id": nuevo_id})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error: {err}"})

@app.route('/api/clientes/<int:id_cliente>', methods=['PUT'])
@login_required
def api_editar_cliente(id_cliente):
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        tipo = data.get("tipo") or data.get("tipo_cliente") or "OCASIONAL"
        estado = data.get("estado", "ACTIVO")
        query = "UPDATE CLIENTE SET nombre=%s, telefono=%s, tipo_cliente=%s, estado=%s WHERE id_cliente=%s"
        valores = (data.get("nombre"), data.get("telefono"), tipo.upper(), estado.upper(), id_cliente)
        cursor.execute(query, valores)
        conn.commit()
        return jsonify({"success": True, "message": "Cliente actualizado"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error: {err}"})

@app.route('/api/clientes/<int:id_cliente>', methods=['DELETE'])
@login_required
def api_eliminar_cliente(id_cliente):
    try: 
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM CLIENTE WHERE id_cliente=%s", (id_cliente,))
        conn.commit()
        return jsonify({"success":True,"message": "Cliente eliminado"})
    except mysql.connector.Error:
        return jsonify({"success":False, "message": "No se puede eliminar, cliente con vehículos registrados"})

# ============================================================
# CRUD API — VEHICULOS
# ============================================================
@app.route('/api/vehiculos/crear', methods=['POST'])
@login_required
def api_crear_vehiculo():
    try:
        datos = request.get_json()
        matricula = datos.get('placa') or datos.get('matricula')
        marca = datos.get('marca')
        modelo = datos.get('modelo')
        color = datos.get('color')
        id_cliente = datos.get('cliente_id') or datos.get('id_cliente')
        if id_cliente == "":
            id_cliente = None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO VEHICULO (placa, marca, modelo, color, id_cliente) VALUES (%s, %s, %s, %s, %s)",
                       (matricula, marca, modelo, color, id_cliente))
        conn.commit()
        return jsonify({'success': True, 'mensaje': 'Vehículo registrado'})
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return jsonify({'success': False, 'error': 'La placa ya está registrada y asignada en el sistema.'})
        return jsonify({'success': False, 'error': f"Error: {err}"}), 500

@app.route('/api/vehiculos/<placa>', methods=['PUT'])
@login_required
def api_editar_vehiculo(placa):
    try:
        datos = request.get_json()
        marca = datos.get('marca')
        modelo = datos.get('modelo')
        color = datos.get('color')
        estado = datos.get('estado', 'ACTIVO')
        id_cliente = datos.get('cliente_id') or None
        if id_cliente == "":
            id_cliente = None

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE VEHICULO SET marca=%s, modelo=%s, color=%s, estado=%s, id_cliente=%s WHERE placa=%s",
                       (marca, modelo, color, estado.upper(), id_cliente, placa))
        conn.commit()
        return jsonify({'success': True, 'message': 'Vehículo actualizado correctamente'})
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return jsonify({'success': False, 'error': 'La nueva placa ingresada ya está en uso.'})
        return jsonify({'success': False, 'error': f"Error: {err}"})

@app.route('/api/vehiculos/<placa>', methods=['DELETE'])
@login_required
def api_eliminar_vehiculo(placa):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM VEHICULO WHERE placa=%s", (placa,))
        conn.commit()
        return jsonify({"success": True, "message": "Vehículo eliminado"})
    except mysql.connector.Error:
        return jsonify({"success": False, "message": "No se puede eliminar: tiene estancias."})

# ============================================================
# CRUD API — ESTANCIAS
# ============================================================
@app.route('/api/estancias', methods=['GET', 'POST'])
@login_required
def api_crear_estancia():
    if request.method == 'GET':
        # Used by app.js cargarEstancias
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT e.id_estancia as id, v.placa as matricula, DATE_FORMAT(e.fecha_entrada, '%Y-%m-%d') as fecha_entrada, TIME_FORMAT(e.fecha_entrada, '%H:%i:%s') as hora_entrada, DATE_FORMAT(e.fecha_salida, '%Y-%m-%d') as fecha_salida, TIME_FORMAT(e.fecha_salida, '%H:%i:%s') as hora_salida, IF(e.fecha_salida IS NULL, 'ACTIVO', 'COMPLETADO') as estado, t.descripcion as tipo, (SELECT monto FROM PAGO p WHERE p.id_estancia = e.id_estancia LIMIT 1) as total
                FROM ESTANCIA e JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo LEFT JOIN TARIFA t ON e.id_tarifa = t.id_tarifa
                ORDER BY e.fecha_salida ASC, e.fecha_entrada DESC
            """)
            res = cursor.fetchall()
            return jsonify(res)
        except mysql.connector.Error as err:
            return jsonify([])

    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True) # Usamos dictionary para facilidad
        matricula = data.get("matricula", "").strip().upper()
        
        if not matricula:
            return jsonify({"success": False, "error": "La matrícula es requerida."})
        
        # 1. Blindaje: Evitar doble entrada
        cursor.execute("SELECT id_vehiculo FROM VEHICULO WHERE placa = %s", (matricula,))
        veh_row = cursor.fetchone()
        if veh_row:
            id_vehiculo = veh_row['id_vehiculo']
            cursor.execute("SELECT id_estancia FROM ESTANCIA WHERE id_vehiculo = %s AND fecha_salida IS NULL", (id_vehiculo,))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "Operación denegada: Este vehículo ya se encuentra dentro del estacionamiento."})
        
        # Continuar con flujo normal
        cursor.execute("SELECT id_vehiculo, id_cliente FROM VEHICULO WHERE placa = %s", (matricula,))
        veh_row = cursor.fetchone()
        
        if not veh_row:
            # Auto-create ghost vehicle
            cursor.execute("INSERT INTO VEHICULO (placa) VALUES (%s)", (matricula,))
            conn.commit()
            id_vehiculo = cursor.lastrowid
            tipo_cliente = 'OCASIONAL'
        else:
            id_vehiculo = veh_row['id_vehiculo']
            id_cliente = veh_row['id_cliente']
            if id_cliente:
                cursor.execute("SELECT tipo_cliente FROM CLIENTE WHERE id_cliente = %s", (id_cliente,))
                cli_row = cursor.fetchone()
                tipo_cliente = cli_row['tipo_cliente'] if cli_row else 'OCASIONAL'
            else:
                tipo_cliente = 'OCASIONAL'

        id_tarifa = data.get("id_tarifa")
        if not id_tarifa:
            cursor.execute("SELECT id_tarifa FROM TARIFA WHERE estado='ACTIVA' AND tipo_cliente_aplicable IN (%s, 'AMBOS') ORDER BY tipo_cliente_aplicable ASC LIMIT 1", (tipo_cliente,))
            tar_row = cursor.fetchone()
            id_tarifa = tar_row['id_tarifa'] if tar_row else 1
        else:
            cursor.execute("SELECT tipo_cliente_aplicable FROM TARIFA WHERE id_tarifa = %s", (id_tarifa,))
            tar_row = cursor.fetchone()
            if tar_row:
                tipo_aplica = tar_row['tipo_cliente_aplicable']
                if tipo_aplica == 'REGISTRADO' and tipo_cliente != 'REGISTRADO':
                    return jsonify({"success": False, "error": "Operación denegada: Tarifa exclusiva para vehículos de Clientes Registrados."})

        cursor.execute("INSERT INTO ESTANCIA (id_vehiculo, fecha_entrada, id_tarifa) VALUES (%s, NOW(), %s)", (id_vehiculo, id_tarifa))
        conn.commit()
        return jsonify({"success": True, "message": f"Entrada registrada para {matricula}"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/estancias/<int:id_estancia>/salida', methods=['POST'])
@login_required
def api_registrar_salida(id_estancia):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        data = request.json or {}
        metodo_pago = data.get('metodo_pago', 'EFECTIVO').upper()

        # Obtener estancia con tarifa asignada y tipo de cliente
        cursor.execute("""
            SELECT e.*, v.placa, c.tipo_cliente,
                   t.costo_hora, t.horas_limite_reduccion, t.costo_hora_reducida
            FROM ESTANCIA e
            JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo
            LEFT JOIN CLIENTE c ON v.id_cliente = c.id_cliente
            LEFT JOIN TARIFA t ON e.id_tarifa = t.id_tarifa
            WHERE e.id_estancia = %s AND e.fecha_salida IS NULL
        """, (id_estancia,))
        servicio = cursor.fetchone()

        if not servicio:
            return jsonify({"ok": False, "msg": "Estancia no encontrada o ya cerrada."})

        ahora = datetime.now()
        minutos_totales = max(1, int((ahora - servicio['fecha_entrada']).total_seconds() / 60))

        # Req 5: Calcular monto por hora completa (redondeo hacia arriba)
        horas = math.ceil(minutos_totales / 60.0)
        if horas < 1:
            horas = 1

        tarifa_base = float(servicio['costo_hora'] or 30.0)
        horas_limite = int(servicio['horas_limite_reduccion'] or 5)
        tarifa_reducida = float(servicio['costo_hora_reducida'] or 25.0)

        if horas <= horas_limite or horas_limite == 0:
            monto_total = horas * tarifa_base
        else:
            monto_total = (horas_limite * tarifa_base) + ((horas - horas_limite) * tarifa_reducida)

        cursor.execute("UPDATE ESTANCIA SET fecha_salida=%s WHERE id_estancia=%s", (ahora, id_estancia))
        cursor.execute("INSERT INTO PAGO (id_estancia, monto, fecha_pago, metodo_pago) VALUES (%s, %s, %s, %s)",
                       (id_estancia, round(monto_total, 2), ahora, metodo_pago))
        conn.commit()

        return jsonify({"ok": True, "total": f"{monto_total:.2f}",
                        "msg": f"Total cobrado: ${monto_total:.2f} ({metodo_pago})"})
    except mysql.connector.Error as err:
        return jsonify({"ok": False, "msg": f"Error: {err}"})

# ============================================================
# CRUD API — TARIFAS
# ============================================================
@app.route('/api/tarifas', methods=['POST'])
@login_required
def api_crear_tarifa():
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO TARIFA (descripcion, costo_hora, horas_limite_reduccion, costo_hora_reducida, tipo_cliente_aplicable) VALUES (%s, %s, %s, %s, %s)",
                       (data.get('descripcion'), float(data.get('costo_hora', 0) or 0), int(data.get('horas_limite_reduccion', 0) or 0), float(data.get('costo_hora_reducida', 0) or 0), data.get('tipo_cliente_aplicable', 'AMBOS')))
        conn.commit()
        return jsonify({'success': True, 'message': 'Tarifa creada exitosamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/tarifas/<int:id_tarifa>', methods=['PUT'])
@login_required
def api_editar_tarifa(id_tarifa):
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE TARIFA SET descripcion=%s, costo_hora=%s, horas_limite_reduccion=%s, costo_hora_reducida=%s, tipo_cliente_aplicable=%s, estado=%s WHERE id_tarifa=%s",
                       (data.get('descripcion'), data.get('costo_hora'), data.get('horas_limite_reduccion'), data.get('costo_hora_reducida'), data.get('tipo_cliente_aplicable'), data.get('estado').upper(), id_tarifa))
        conn.commit()
        return jsonify({'success': True, 'message': 'Tarifa actualizada correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================
# CRUD API — PENSIONES
# ============================================================
@app.route('/api/pensiones', methods=['POST'])
@login_required
def api_crear_pension():
    data = request.json
    try:
        fecha_inicio = data.get("fecha_inicio")
        fecha_fin    = data.get("fecha_fin")
        id_vehiculo  = data.get("vehiculo_id")

        if not id_vehiculo or not fecha_inicio or not fecha_fin:
            return jsonify({"success": False, "error": "Datos incompletos. Se requieren fechas y vehículo."})

        # Validación backend de fechas
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        ff = datetime.strptime(fecha_fin,    "%Y-%m-%d")
        if ff <= fi:
            return jsonify({"success": False, "error": "La fecha de fin debe ser posterior a la fecha de inicio."})

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. Blindaje: Evitar pensiones traslapadas activas
        cursor.execute("SELECT id_pension FROM PENSION WHERE id_vehiculo = %s AND estado = 'ACTIVA'", (id_vehiculo,))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Operación denegada: Este vehículo ya tiene una pensión ACTIVA. Cancélela antes de registrar una nueva."})
        
        id_cliente   = data.get("cliente_id")
        
        # Si no nos pasaron cliente pero sí vehículo, inferir el cliente
        if id_vehiculo and not id_cliente:
            cursor.execute("SELECT id_cliente FROM VEHICULO WHERE id_vehiculo = %s", (id_vehiculo,))
            veh_row = cursor.fetchone()
            if veh_row:
                id_cliente = veh_row['id_cliente']

        costo        = float(data.get("monto", data.get("costo_mensual", PENSION_MENSUAL_BASE)))
        metodo_pago  = data.get("metodo_pago", "EFECTIVO").upper()

        # Req 6: Descuento 20% para clientes con más de 2 años de antigüedad
        cursor.execute("SELECT fecha_registro FROM CLIENTE WHERE id_cliente = %s", (id_cliente,))
        cliente = cursor.fetchone()
        descuento_aplicado = False
        if cliente and cliente['fecha_registro']:
            anios = (datetime.now() - cliente['fecha_registro']).days / 365.25
            if anios > 2:
                costo *= 0.80
                descuento_aplicado = True

        cursor.execute("INSERT INTO PENSION (id_cliente, id_vehiculo, fecha_inicio, fecha_fin, costo_mensual) VALUES (%s, %s, %s, %s, %s)",
                       (id_cliente, id_vehiculo, fecha_inicio, fecha_fin, costo))
        pension_id = cursor.lastrowid
        cursor.execute("INSERT INTO PAGO (id_pension, monto, fecha_pago, metodo_pago) VALUES (%s, %s, NOW(), %s)",
                       (pension_id, costo, metodo_pago))
        conn.commit()
        msg = "Pensión registrada con 20% de descuento por lealtad" if descuento_aplicado else "Pensión registrada"
        return jsonify({"success": True, "message": msg})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/pensiones/<int:id_pension>', methods=['PUT'])
@login_required
def api_editar_pension(id_pension):
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        id_cliente = data.get("cliente_id")
        id_vehiculo = data.get("vehiculo_id")
        fecha_inicio = data.get("fecha_inicio")
        fecha_fin = data.get("fecha_fin")
        monto = float(data.get("monto", data.get("costo_mensual", 0.0)))
        estado = data.get("estatus", data.get("estado", "ACTIVA"))

        # 3. Blindaje: Validar fechas en edición
        if fecha_inicio and fecha_fin:
            fi = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            ff = datetime.strptime(fecha_fin,    "%Y-%m-%d")
            if ff <= fi:
                return jsonify({"success": False, "error": "La fecha de fin debe ser posterior a la fecha de inicio."})

        # 4. Blindaje: Evitar traslapes en edición si se activa
        if id_vehiculo and estado == 'ACTIVA':
            cursor.execute("SELECT id_pension FROM PENSION WHERE id_vehiculo = %s AND estado = 'ACTIVA' AND id_pension != %s", (id_vehiculo, id_pension))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "Operación denegada: El vehículo ya tiene OTRA pensión activa."})

        if id_vehiculo and not id_cliente:
            cursor.execute("SELECT id_cliente FROM VEHICULO WHERE id_vehiculo = %s", (id_vehiculo,))
            veh_row = cursor.fetchone()
            if veh_row:
                id_cliente = veh_row['id_cliente']

        cursor.execute("UPDATE PENSION SET fecha_inicio=%s, fecha_fin=%s, costo_mensual=%s, estado=%s, id_vehiculo=%s, id_cliente=%s WHERE id_pension=%s",
                       (fecha_inicio, fecha_fin, monto, estado, id_vehiculo, id_cliente, id_pension))
        conn.commit()
        return jsonify({"success": True, "message": "Pensión actualizada"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/pensiones/<int:id_pension>', methods=['DELETE'])
@login_required
def api_eliminar_pension(id_pension):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE PENSION SET estado='CANCELADA' WHERE id_pension=%s", (id_pension,))
        conn.commit()
        return jsonify({"success": True, "message": "Pensión cancelada"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})



# ============================================================
# CRUD API — USUARIOS
# ============================================================
@app.route('/api/usuarios', methods=['POST'])
@admin_required
def api_crear_usuario():
    data = request.json
    raw_pw = data.get("password", "")
    if not raw_pw:
        return jsonify({"success": False, "error": "La contraseña no puede estar vacía"})
    try:
        conn = get_db()
        cursor = conn.cursor()
        hashed = generate_password_hash(raw_pw)
        cursor.execute("INSERT INTO USUARIO (nombre, email, username, password, perfil) VALUES (%s, %s, %s, %s, %s)",
                       (data.get("nombre", ""), data.get("email", ""), data.get("username", ""), hashed, data.get("perfil", "cobrador")))
        conn.commit()
        return jsonify({"success": True, "message": "Usuario creado"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/usuarios/<int:id_usuario>', methods=['PUT'])
@admin_required
def api_editar_usuario(id_usuario):
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        if data.get("password"):
            hashed = generate_password_hash(data.get("password"))
            cursor.execute("UPDATE USUARIO SET nombre=%s, email=%s, username=%s, password=%s, perfil=%s WHERE id_usuario=%s",
                           (data.get("nombre"), data.get("email"), data.get("username"), hashed, data.get("perfil"), id_usuario))
        else:
            cursor.execute("UPDATE USUARIO SET nombre=%s, email=%s, username=%s, perfil=%s WHERE id_usuario=%s",
                           (data.get("nombre"), data.get("email"), data.get("username"), data.get("perfil"), id_usuario))
        conn.commit()
        return jsonify({"success": True, "message": "Usuario actualizado"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/usuarios/<int:id_usuario>', methods=['DELETE'])
@admin_required
def api_eliminar_usuario(id_usuario):
    if id_usuario == session.get('user', {}).get('id_usuario'):
        return jsonify({"success": False, "error": "No puedes eliminar tu propia cuenta"})
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM USUARIO WHERE id_usuario=%s", (id_usuario,))
        conn.commit()
        return jsonify({"success": True, "message": "Usuario eliminado"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": "No se puede eliminar, tiene dependencias"})

# ============================================================
# STATS API
# ============================================================
@app.route('/api/stats')
@login_required
def api_stats():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM ESTANCIA WHERE fecha_salida IS NULL")
        vehiculos_dentro = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM CLIENTE")
        total_clientes = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM PENSION WHERE estado = 'ACTIVA'")
        pensiones_activas = cursor.fetchone()['count']
        
        cursor.execute("SELECT SUM(monto) as total FROM PAGO WHERE DATE(fecha_pago) = CURDATE()")
        res = cursor.fetchone()
        ingresos_hoy = res['total'] if res and res['total'] else 0.0

        return jsonify({
            "success": True,
            "vehiculos_dentro": vehiculos_dentro,
            "total_clientes": total_clientes,
            "pensiones_activas": pensiones_activas,
            "ingresos_hoy": float(ingresos_hoy)
        })
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": str(err)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
