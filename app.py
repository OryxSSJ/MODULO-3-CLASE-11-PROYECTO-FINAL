
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
from functools import wraps
import mysql.connector
from datetime import datetime, timedelta
import os, math

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ============================================================
# Configuracion de la db
# ============================================================
DB_CONFIG ={
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'estacionamiento_db'
}

# ============================================================
# AUTH DECORATORS
# ============================================================
<<<<<<< Updated upstream
def get_db():
    """Establece y retorna la conexion a la base de datos de forma global y segura"""
    if 'db' not in g:
        g.db = mysql.connector.connect(**DB_CONFIG)
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Asegura que la conexion se cierre al terminar la peticion, evitando leaks"""
    db = g.pop('db', None)
    if db is not None:
        db.close()
=======
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
# ============================================================
# CONTEXTO GLOBAL PARA TODAS LAS PLANTILLAS
# ============================================================
@app.context_processor
def inject_global_stats():
    # Solo ejecutar si el usuario ha iniciado sesión
    if 'user' not in session:
        return dict(global_stats={})
        
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # 1. Vehículos dentro (estancias activas sin hora de salida)
        cursor.execute("SELECT COUNT(*) as count FROM Servicios WHERE hora_salida IS NULL")
        vehiculos_dentro = cursor.fetchone()['count']
        
        # 2. Total clientes
        cursor.execute("SELECT COUNT(*) as count FROM Clientes")
        total_clientes = cursor.fetchone()['count']
        
        # 3. Pensiones activas
        cursor.execute("SELECT COUNT(*) as count FROM Pensiones WHERE estatus = 'ACTIVA'")
        pensiones_activas = cursor.fetchone()['count']
        
        # 4. Ingresos hoy
        cursor.execute("""
            SELECT COALESCE(SUM(monto_total), 0) as total 
            FROM Cobros 
            WHERE DATE(fecha_cobro) = CURDATE()
        """)
        ingresos_hoy = cursor.fetchone()['total']
        
        cursor.close()
        
        return dict(global_stats={
            'vehiculos_dentro': vehiculos_dentro,
            'total_clientes': total_clientes,
            'pensiones_activas': pensiones_activas,
            'ingresos_hoy': float(ingresos_hoy)
        })
    except Exception as e:
        print("Error en context_processor:", e)
        return dict(global_stats={
            'vehiculos_dentro': 0, 'total_clientes': 0, 'pensiones_activas': 0, 'ingresos_hoy': 0.0
        })


=======
>>>>>>> Stashed changes
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
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True) 
            query = "SELECT * FROM USUARIO WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            if user:
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

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True, buffered=True)

<<<<<<< Updated upstream
        # Estancias activas para la tabla del dashboard (LEFT JOIN porque Precios puede estar vacía)
        cursor.execute("""
            SELECT s.folio_servicio, s.matricula, s.fecha_entrada, s.hora_entrada,
                   COALESCE(p.tipo, 'cajon') as tipo
            FROM Servicios s
            LEFT JOIN Precios p ON s.folio_precio = p.folio_precio
            WHERE s.hora_salida IS NULL
            ORDER BY s.fecha_entrada DESC, s.hora_entrada DESC
        """)
=======
        cursor.execute("SELECT COUNT(*) as vehiculos_dentro FROM ESTANCIA WHERE fecha_salida IS NULL")
        vehiculos_dentro = cursor.fetchone()['vehiculos_dentro']
        
        cursor.execute("SELECT COUNT(*) as total_clientes FROM CLIENTE")
        total_clientes = cursor.fetchone()['total_clientes']
        
        cursor.execute("""
            SELECT SUM(monto) as ingresos_hoy 
            FROM PAGO 
            WHERE DATE(fecha_pago) = CURDATE()
        """)
        resultado_ingresos = cursor.fetchone()
        ingresos_hoy = resultado_ingresos['ingresos_hoy'] if resultado_ingresos and resultado_ingresos['ingresos_hoy'] else 0

        stats = {
            'ingresos_hoy': float(ingresos_hoy),
        }
        
        cursor.execute("""
        SELECT e.id_estancia as folio_servicio, v.placa as matricula, DATE(e.fecha_entrada) as fecha_entrada, TIME(e.fecha_entrada) as hora_entrada, t.descripcion as tipo
        FROM ESTANCIA e
        JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo
        LEFT JOIN TARIFA t ON e.id_tarifa = t.id_tarifa
        WHERE e.fecha_salida IS NULL""")
>>>>>>> Stashed changes
        estancias_activas = cursor.fetchall()
        cursor.close()
<<<<<<< Updated upstream

        # Las stats del dashboard ahora vienen del context_processor global (global_stats)
        # No duplicamos queries — todo el sistema lee de la misma fuente de verdad
        return render_template('dashboard.html', estancias_activas=estancias_activas)
=======
        conn.close()
        return render_template('dashboard.html', stats=stats, estancias_activas=estancias_activas)
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        flash(f'Error de DB: {err}', 'error')
        return render_template('dashboard.html', estancias_activas=[])

@app.route('/clientes')
@login_required
def clientes():
    try:
      conn = get_db()
      cursor = conn.cursor(dictionary=True)
      cursor.execute("SELECT id_cliente as id, nombre, telefono, tipo_cliente, fecha_registro, estado FROM CLIENTE")
      lista_clientes = cursor.fetchall()
<<<<<<< Updated upstream
  
      return render_template('clientes.html', clientes = lista_clientes)
=======
      cursor.close()
      conn.close()  
      return render_template('clientes.html', clientes=lista_clientes)
>>>>>>> Stashed changes
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
            SELECT v.id_vehiculo as matricula_id, v.placa as matricula, v.marca, v.modelo, v.color, v.id_cliente as cliente_id, c.nombre as nombre_cliente 
            FROM VEHICULO v 
            LEFT JOIN CLIENTE c ON v.id_cliente = c.id_cliente
        """)
        lista_vehiculos = cursor.fetchall()
        
<<<<<<< Updated upstream
        # También necesitamos la lista de clientes para el "select/dropdown" al registrar un vehículo
        cursor.execute("SELECT cliente_id, nombre, estado FROM Clientes")
=======
        cursor.execute("SELECT id_cliente as cliente_id, nombre FROM CLIENTE")
>>>>>>> Stashed changes
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
                   t.costo_inicial as precio, t.descripcion as nombre_tarifa 
            FROM ESTANCIA e
            JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo
            LEFT JOIN TARIFA t ON e.id_tarifa = t.id_tarifa
            ORDER BY e.fecha_salida ASC, e.fecha_entrada DESC
        """)
        lista_estancias = cursor.fetchall()
        
        cursor.execute("SELECT placa as matricula FROM VEHICULO")
        lista_vehiculos = cursor.fetchall()
        
        cursor.execute("SELECT id_tarifa as folio_precio, descripcion as tipo, costo_inicial as precio FROM TARIFA WHERE estado = 'ACTIVA'")
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
            SELECT p.id_pago as folio_cobro, p.id_estancia as folio_servicio, v.placa as matricula, 
                   TIME(e.fecha_salida) as hora_estancia, p.monto as monto_total, p.fecha_pago as fecha_cobro,
                   'Sistema' as cobrador
            FROM PAGO p
            LEFT JOIN ESTANCIA e ON p.id_estancia = e.id_estancia
            LEFT JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo
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
            SELECT p.id_pension as pension_id, p.id_cliente as cliente_id, p.fecha_inicio, p.fecha_fin, p.costo_mensual as monto, p.estado as estatus, c.nombre as nombre_cliente 
            FROM PENSION p
            JOIN CLIENTE c ON p.id_cliente = c.id_cliente
        """)
        lista_pensiones = cursor.fetchall()
        
<<<<<<< Updated upstream
        # Para el formulario de "Nueva Pensión" necesitamos la lista de clientes
        cursor.execute("SELECT cliente_id, nombre, estado FROM Clientes")
=======
        cursor.execute("SELECT id_cliente as cliente_id, nombre FROM CLIENTE")
>>>>>>> Stashed changes
        lista_clientes = cursor.fetchall()
        
        return render_template('pensiones.html', pensiones=lista_pensiones, clientes=lista_clientes)
    except mysql.connector.Error as err:
        flash(f'Error al cargar pensiones: {err}', 'error')
        return render_template('pensiones.html', pensiones=[], clientes=[])

@app.route('/tarifas')
@login_required
def tarifas():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_tarifa as folio_precio, descripcion as tipo, costo_inicial as precio FROM TARIFA")
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
    return render_template('reportes.html')

# ============================================================
# REPORTES API (REQ 7, 8, 9, 10)
# ============================================================
@app.route('/api/reportes_datos')
@admin_required
def api_reportes_datos():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Entradas y salidas por mes (año actual)
        cursor.execute("""
            SELECT MONTH(fecha_entrada) as mes, COUNT(*) as entradas, 
                   COUNT(fecha_salida) as salidas
            FROM ESTANCIA 
            WHERE YEAR(fecha_entrada) = YEAR(CURDATE())
            GROUP BY MONTH(fecha_entrada)
        """)
        es_por_mes = cursor.fetchall()
        
        # 2. Meses con mayor demanda
        cursor.execute("""
            SELECT MONTH(fecha_entrada) as mes, COUNT(*) as total_servicios
            FROM ESTANCIA 
            WHERE YEAR(fecha_entrada) = YEAR(CURDATE())
            GROUP BY MONTH(fecha_entrada)
            ORDER BY total_servicios DESC
            LIMIT 3
        """)
        meses_demanda = cursor.fetchall()
        
<<<<<<< Updated upstream
        
        return render_template('reportes.html', ingresos=ingresos_recientes)
=======
        # 3. Horarios con mayor demanda
        cursor.execute("""
            SELECT HOUR(fecha_entrada) as hora, COUNT(*) as cantidad
            FROM ESTANCIA 
            WHERE YEAR(fecha_entrada) = YEAR(CURDATE())
            GROUP BY HOUR(fecha_entrada)
            ORDER BY cantidad DESC
        """)
        horas_demanda = cursor.fetchall()
        
        # 4. Ingresos
        cursor.execute("""
            SELECT MONTH(fecha_pago) as mes, 
                   SUM(CASE WHEN id_estancia IS NOT NULL THEN monto ELSE 0 END) as ingresos_cajon,
                   SUM(CASE WHEN id_pension IS NOT NULL THEN monto ELSE 0 END) as ingresos_pension
            FROM PAGO
            WHERE YEAR(fecha_pago) = YEAR(CURDATE())
            GROUP BY MONTH(fecha_pago)
        """)
        ingresos_mes = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify({
            "success": True, 
            "es_por_mes": es_por_mes,
            "meses_demanda": meses_demanda,
            "horas_demanda": horas_demanda,
            "ingresos_mes": ingresos_mes
        })
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": str(err)})

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
<<<<<<< Updated upstream
        query = """INSERT INTO Clientes (nombre, telefono, email, rfc, usuario_id, tipo, estado)
                   VALUES ( %s, %s, %s, %s, %s, %s, %s)"""
        #obetner el id de usuario logeado y registrando al cliente
        usuario_id = session['user']['usuario_id']
        valores = (
            data.get("nombre", ""),
            data.get("telefono", ""),
            data.get("email", ""),
            data.get("rfc", ""),
            usuario_id,
            data.get("tipo", "registrado"),
            data.get("estado", "activo")
        )
        cursor.execute(query, valores)
        conn.commit()
        nuevo_id = cursor.lastrowid
        return jsonify({"success": True, "message": "Cliente registrado correctamente", "id": nuevo_id})
=======
        query = "INSERT INTO CLIENTE (nombre, telefono, tipo_cliente) VALUES (%s, %s, %s)"
        valores = (data.get("nombre", ""), data.get("telefono", ""), data.get("tipo_cliente", "OCASIONAL"))
        cursor.execute(query, valores)
        conn.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Cliente registrado", "id": nuevo_id})
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error: {err}"})

@app.route('/api/clientes/<int:id_cliente>', methods=['PUT'])
@login_required
def api_editar_cliente(id_cliente):
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
<<<<<<< Updated upstream
        query = """UPDATE Clientes
                   SET nombre=%s, telefono=%s, email=%s, rfc=%s, tipo=%s, estado=%s
                   WHERE cliente_id=%s"""
        valores = (
            data.get("nombre"),
            data.get("telefono"),
            data.get("email"),
            data.get("rfc"),
            data.get("tipo", "registrado"),
            data.get("estado", "activo"),
            id_cliente)
        cursor.execute(query, valores)
        conn.commit()
        return jsonify({"success": True, "message": "Cliente actualizado correctamente"})
=======
        query = "UPDATE CLIENTE SET nombre=%s, telefono=%s, tipo_cliente=%s, estado=%s WHERE id_cliente=%s"
        valores = (data.get("nombre"), data.get("telefono"), data.get("tipo_cliente"), data.get("estado"), id_cliente)
        cursor.execute(query, valores)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Cliente actualizado"})
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        return jsonify({"success":True,"message": "Cliente eliminado correctamente"})
    except mysql.connector.Error as err:
        #Si hay vehiculos registrados mysql bloqueara el borrado por llave foranea, hacer un trigger
        return jsonify({"success":False, "message": "No se puede eliminar, cliente con vehiculos registrados"})


=======
        cursor.close()
        conn.close()
        return jsonify({"success":True,"message": "Cliente eliminado"})
    except mysql.connector.Error:
        return jsonify({"success":False, "message": "No se puede eliminar, cliente con vehículos registrados"})
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
        id_cliente = datos.get('cliente_id')
        if not id_cliente: # Handle occasional
            id_cliente = None

        # 2. Conectamos a la BD usando tu función estándar
        conn = get_db()
=======
        id_cliente = datos.get('cliente_id') or datos.get('id_cliente')

        conn = get_db_connection()
>>>>>>> Stashed changes
        cursor = conn.cursor()
        cursor.execute("INSERT INTO VEHICULO (placa, marca, modelo, color, id_cliente) VALUES (%s, %s, %s, %s, %s)",
                       (matricula, marca, modelo, color, id_cliente))
        conn.commit()
<<<<<<< Updated upstream

        # 3. Respuesta de éxito
        return jsonify({'success': True, 'mensaje': 'Vehículo registrado correctamente'})

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'error': f"Error de BD: {err}"}), 500
    except Exception as e:
        print("Error en /api/vehiculos/crear:", e)
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/vehiculos/<string:matricula>', methods=['PUT'])
=======
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'mensaje': 'Vehículo registrado'})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'error': f"Error: {err}"}), 500

@app.route('/api/vehiculos/<placa>', methods=['DELETE'])
>>>>>>> Stashed changes
@login_required
def api_eliminar_vehiculo(placa):
    try:
        conn = get_db()
        cursor = conn.cursor()
<<<<<<< Updated upstream
        
        # No actualizamos la matrícula porque es la llave primaria, solo el resto de los datos
        query = """UPDATE Vehiculos 
                   SET modelo=%s, marca=%s, color=%s, cliente_id=%s 
                   WHERE matricula=%s"""
        
        cliente_id = data.get("cliente_id")
        if not cliente_id:
            cliente_id = None
            
        valores = (
            data.get("modelo"),
            data.get("marca"),
            data.get("color"),
            cliente_id,
            matricula
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        return jsonify({"success": True, "message": "Vehículo actualizado correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})


@app.route('/api/vehiculos/<string:matricula>', methods=['DELETE'])
@login_required
def api_eliminar_vehiculo(matricula):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Eliminamos buscando por la matrícula (string)
        cursor.execute("DELETE FROM Vehiculos WHERE matricula=%s", (matricula,))
        conn.commit()
        
        return jsonify({"success": True, "message": "Vehículo eliminado correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": "No se puede eliminar: el vehículo tiene servicios/cobros registrados."})

=======
        cursor.execute("DELETE FROM VEHICULO WHERE placa=%s", (placa,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Vehículo eliminado"})
    except mysql.connector.Error:
        return jsonify({"success": False, "message": "No se puede eliminar: tiene estancias."})
>>>>>>> Stashed changes

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
                SELECT e.id_estancia as id, v.placa as matricula, DATE(e.fecha_entrada) as fecha_entrada, TIME(e.fecha_entrada) as hora_entrada, DATE(e.fecha_salida) as fecha_salida, TIME(e.fecha_salida) as hora_salida, IF(e.fecha_salida IS NULL, 'ACTIVO', 'COMPLETADO') as estado, t.descripcion as tipo, (SELECT monto FROM PAGO p WHERE p.id_estancia = e.id_estancia LIMIT 1) as total
                FROM ESTANCIA e JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo LEFT JOIN TARIFA t ON e.id_tarifa = t.id_tarifa
                ORDER BY e.fecha_salida ASC, e.fecha_entrada DESC
            """)
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify(res)
        except mysql.connector.Error as err:
            return jsonify([])

    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        matricula = data.get("matricula").upper()
        
        # Check if vehicle exists, if not, wait we should error? The UI requires vehicle registration now or just accepts plate?
        # estancias.html modal just asks for matricula and tipo.
        # In new schema, ESTANCIA requires id_vehiculo. So we MUST ensure vehicle exists.
        cursor.execute("SELECT id_vehiculo FROM VEHICULO WHERE placa = %s", (matricula,))
        veh_row = cursor.fetchone()
        
        if not veh_row:
            # Auto-create ghost vehicle
            cursor.execute("INSERT INTO VEHICULO (placa) VALUES (%s)", (matricula,))
            conn.commit()
            id_vehiculo = cursor.lastrowid
        else:
            id_vehiculo = veh_row[0]

        cursor.execute("INSERT INTO ESTANCIA (id_vehiculo, fecha_entrada, id_tarifa) VALUES (%s, NOW(), (SELECT MIN(id_tarifa) FROM TARIFA WHERE estado='ACTIVA'))", (id_vehiculo,))
        conn.commit()
<<<<<<< Updated upstream
        
        return jsonify({"success": True, "message": f"Entrada registrada para el vehículo {valores[0]}"})
        
=======
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": f"Entrada registrada para {matricula}"})
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/estancias/<int:id_estancia>/salida', methods=['POST'])
@login_required
def api_registrar_salida(id_estancia):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # REQ 5 logic
        cursor.execute("""
            SELECT e.*, v.placa, c.tipo_cliente 
            FROM ESTANCIA e 
            JOIN VEHICULO v ON e.id_vehiculo = v.id_vehiculo 
            LEFT JOIN CLIENTE c ON v.id_cliente = c.id_cliente
            WHERE e.id_estancia = %s AND e.fecha_salida IS NULL
        """, (id_estancia,))
        servicio = cursor.fetchone()
        
        if not servicio:
            return jsonify({"success": False, "error": "Estancia no encontrada o ya cerrada."})
            
        ahora = datetime.now()
        dt_entrada = servicio['fecha_entrada']
        tiempo_estancia = ahora - dt_entrada
        minutos_totales = int(tiempo_estancia.total_seconds() / 60)
        horas_cobrables = math.ceil(minutos_totales / 60)
        if horas_cobrables == 0: horas_cobrables = 1
            
        # Lógica Req 5
        if servicio.get('tipo_cliente') == 'REGISTRADO':
            tarifa_base = 26.0
            tarifa_reducida = 22.0
        else:
            tarifa_base = 30.0
            tarifa_reducida = 25.0
            
        if horas_cobrables <= 5:
            monto_total = horas_cobrables * tarifa_base
        else:
            monto_total = (5 * tarifa_base) + ((horas_cobrables - 5) * tarifa_reducida)
            
        # Actualizar Estancia
        cursor.execute("UPDATE ESTANCIA SET fecha_salida = %s WHERE id_estancia = %s", (ahora, id_estancia))
        
        # Insertar Pago
        cursor.execute("INSERT INTO PAGO (id_estancia, monto, fecha_pago, metodo_pago) VALUES (%s, %s, %s, %s)", 
                       (id_estancia, monto_total, ahora, 'EFECTIVO'))
        
        conn.commit()
        
        return jsonify({
            "success": True, 
            "total": f"{monto_total:.2f}",
            "message": f"Total a cobrar: ${monto_total:.2f}"
        })
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

# ============================================================
# CRUD API — PENSIONES
# ============================================================
@app.route('/api/pensiones', methods=['POST'])
@login_required
def api_crear_pension():
    data = request.json
    try:
<<<<<<< Updated upstream
        conn = get_db()
        cursor = conn.cursor()
        
        query = """INSERT INTO Pensiones (cliente_id, matricula, fecha_inicio, fecha_fin, monto, estatus) 
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        valores = (
            data.get("cliente_id"),
            data.get("matricula").upper(),
            data.get("fecha_inicio"),
            data.get("fecha_fin"),
            float(data.get("monto", 0.0)),
            "ACTIVA"
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        return jsonify({"success": True, "message": "Pensión registrada correctamente"})
        
=======
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        id_cliente = data.get("cliente_id")
        costo = float(data.get("costo_mensual", 0.0))
        
        # Req 6: Descuento para clientes con más de 2 años
        cursor.execute("SELECT fecha_registro FROM CLIENTE WHERE id_cliente = %s", (id_cliente,))
        cliente = cursor.fetchone()
        if cliente and cliente['fecha_registro']:
            anios_antiguedad = (datetime.now() - cliente['fecha_registro']).days / 365.25
            if anios_antiguedad > 2:
                costo = costo * 0.80 # 20% descuento
                
        cursor.execute("INSERT INTO PENSION (id_cliente, fecha_inicio, fecha_fin, costo_mensual) VALUES (%s, %s, %s, %s)",
                       (id_cliente, data.get("fecha_inicio"), data.get("fecha_fin"), costo))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Pensión registrada con descuento por lealtad" if cliente and cliente['fecha_registro'] and anios_antiguedad > 2 else "Pensión registrada"})
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/pensiones/<int:id_pension>', methods=['PUT'])
@login_required
def api_editar_pension(id_pension):
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
<<<<<<< Updated upstream
        
        query = """UPDATE Pensiones 
                   SET cliente_id=%s, matricula=%s, fecha_inicio=%s, fecha_fin=%s, monto=%s, estatus=%s 
                   WHERE id_pension=%s"""
        valores = (
            data.get("cliente_id"),
            data.get("matricula").upper() if data.get("matricula") else "",
            data.get("fecha_inicio"),
            data.get("fecha_fin"),
            float(data.get("monto", 0.0)),
            data.get("estatus", "ACTIVA"),
            pension_id
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        return jsonify({"success": True, "message": "Pensión actualizada correctamente"})
        
=======
        cursor.execute("UPDATE PENSION SET fecha_inicio=%s, fecha_fin=%s, costo_mensual=%s, estado=%s WHERE id_pension=%s",
                       (data.get("fecha_inicio"), data.get("fecha_fin"), float(data.get("costo_mensual", 0.0)), data.get("estado", "ACTIVA"), id_pension))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Pensión actualizada"})
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/pensiones/<int:id_pension>', methods=['DELETE'])
@login_required
def api_eliminar_pension(id_pension):
    try:
        conn = get_db()
        cursor = conn.cursor()
<<<<<<< Updated upstream
        
        # En lugar de borrar el registro (para no perder el historial), es mejor cambiar el estado a CANCELADA
        cursor.execute("UPDATE Pensiones SET estatus='CANCELADA' WHERE id_pension=%s", (pension_id,))
        conn.commit()
        
        return jsonify({"success": True, "message": "Pensión cancelada correctamente"})
        
=======
        cursor.execute("UPDATE PENSION SET estado='CANCELADA' WHERE id_pension=%s", (id_pension,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Pensión cancelada"})
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

# ============================================================
# CRUD API — TARIFAS
# ============================================================
@app.route('/api/tarifas', methods=['POST'])
@login_required
def api_crear_tarifa():
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO TARIFA (descripcion, costo_inicial) VALUES (%s, %s)", (data.get("tipo", "General"), float(data.get("precio", 0.0))))
        conn.commit()
<<<<<<< Updated upstream
        
        return jsonify({"success": True, "message": "Tarifa creada correctamente"})
        
=======
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Tarifa creada"})
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

@app.route('/api/tarifas/<int:id_tarifa>', methods=['PUT'])
@login_required
def api_editar_tarifa(id_tarifa):
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE TARIFA SET descripcion=%s, costo_inicial=%s WHERE id_tarifa=%s", (data.get("tipo"), float(data.get("precio", 0.0)), id_tarifa))
        conn.commit()
<<<<<<< Updated upstream
        
        return jsonify({"success": True, "message": "Tarifa actualizada correctamente"})
        
=======
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Tarifa actualizada"})
>>>>>>> Stashed changes
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Error: {err}"})

# ============================================================
# CRUD API — USUARIOS
# ============================================================
@app.route('/api/usuarios', methods=['POST'])
@admin_required
def api_crear_usuario():
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO USUARIO (nombre, email, username, password, perfil) VALUES (%s, %s, %s, %s, %s)",
                       (data.get("nombre", ""), data.get("email", ""), data.get("username", ""), data.get("password", ""), data.get("perfil", "cobrador")))
        conn.commit()
<<<<<<< Updated upstream
        
        return jsonify({"success": True, "message": "Usuario creado correctamente"})
        
=======
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuario creado"})
>>>>>>> Stashed changes
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
            cursor.execute("UPDATE USUARIO SET nombre=%s, email=%s, username=%s, password=%s, perfil=%s WHERE id_usuario=%s",
                           (data.get("nombre"), data.get("email"), data.get("username"), data.get("password"), data.get("perfil"), id_usuario))
        else:
            cursor.execute("UPDATE USUARIO SET nombre=%s, email=%s, username=%s, perfil=%s WHERE id_usuario=%s",
                           (data.get("nombre"), data.get("email"), data.get("username"), data.get("perfil"), id_usuario))
        conn.commit()
<<<<<<< Updated upstream
        
        return jsonify({"success": True, "message": "Usuario actualizado correctamente"})
        
=======
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuario actualizado"})
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        
        return jsonify({"success": True, "message": "Usuario eliminado correctamente"})
        
=======
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuario eliminado"})
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
        
=======
        cursor.close()
        conn.close()
>>>>>>> Stashed changes
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
