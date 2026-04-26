from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
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
def get_db_connection():
    """Establece y retorna la conexion a la base de datos"""
    return mysql.connector.connect(**DB_CONFIG)

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
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True) 
            
            # evitar SQL injection
            query = "SELECT * FROM Usuarios WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #1 vehiculos dentro
        cursor.execute("SELECT COUNT(*) as vehiculos_dentro FROM Servicios WHERE hora_salida IS NULL")
        vehiculos_dentro = cursor.fetchone()['vehiculos_dentro']
        #2 total clientes registrados
        cursor.execute("SELECT COUNT(*) as total_clientes FROM Clientes")
        total_clientes = cursor.fetchone()['total_clientes']
        #3 ingresos dia de hoy
        hoy = datetime.now().strftime("%Y-%m-%d")
        # Obtenemos los ingresos del día de hoy
        cursor.execute("""
            SELECT SUM(monto_total) as ingresos_hoy 
            FROM cobros 
            WHERE DATE(fecha_cobro) = CURDATE()
        """)
        resultado_ingresos = cursor.fetchone()
        
        # Si no hay cobros hoy, 'ingresos_hoy' será None. Lo convertimos a 0 de forma segura.
        ingresos_hoy = 0
        if resultado_ingresos and resultado_ingresos['ingresos_hoy'] is not None:
            ingresos_hoy = resultado_ingresos['ingresos_hoy']

        # Mandamos los datos al diccionario stats
        stats = {
            'ingresos_hoy': ingresos_hoy,
            # Aquí dejas las demás variables que ya tenías en tu stats (entradas, salidas, etc)
        }
        # servicios activos
        cursor.execute("""
        SELECT s.folio_servicio, s.matricula, s.fecha_entrada, s.hora_entrada, p.tipo
        FROM Servicios s
        JOIN Precios p ON s.folio_precio = p.folio_precio
        WHERE s.hora_salida IS NULL""")
        estancias_activas = cursor.fetchall()

        cursor.close()
        conn.close()
        return render_template('dashboard.html', stats=stats,
                               estancias_activas = estancias_activas)
    except mysql.connector.Error as err:
        flash(f'Error de DB: {err}', 'error')
        return render_template('dashboard.html', stats={}, estancias_activas=[])


@app.route('/clientes')
@login_required
def clientes():
    try:
      conn = get_db_connection()
      cursor = conn.cursor(dictionary=True)
      #Todos los clientes
      cursor.execute("SELECT * FROM Clientes")
      lista_clientes = cursor.fetchall()
      cursor.close()
      conn.close()  
      return render_template('clientes.html', clientes = lista_clientes)
    except mysql.connector.Error as err:
        flash(f'Error al cargar clientes: {err}', 'error')

    return render_template('clientes.html', clientes=[])


@app.route('/vehiculos')
@login_required
def vehiculos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Traemos vehículos haciendo un JOIN con Clientes para mostrar el nombre del dueño
        cursor.execute("""
            SELECT v.*, c.nombre as nombre_cliente 
            FROM Vehiculos v 
            LEFT JOIN Clientes c ON v.cliente_id = c.cliente_id
        """)
        lista_vehiculos = cursor.fetchall()
        
        # También necesitamos la lista de clientes para el "select/dropdown" al registrar un vehículo
        cursor.execute("SELECT cliente_id, nombre FROM Clientes")
        lista_clientes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('vehiculos.html', vehiculos=lista_vehiculos, clientes=lista_clientes)
    except mysql.connector.Error as err:
        flash(f'Error al cargar vehículos: {err}', 'error')
        return render_template('vehiculos.html', vehiculos=[], clientes=[])


@app.route('/estancias')
@login_required
def estancias():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Traemos todos los servicios, mostrando primero los que no han salido
        cursor.execute("""
            SELECT s.*, p.precio, p.tipo as nombre_tarifa 
            FROM Servicios s
            LEFT JOIN Precios p ON s.folio_precio = p.folio_precio
            ORDER BY s.fecha_salida ASC, s.fecha_entrada DESC, s.hora_entrada DESC
        """)
        lista_estancias = cursor.fetchall()
        
        # Necesitamos las matrículas registradas para el select de "Nueva Entrada"
        cursor.execute("SELECT matricula FROM Vehiculos")
        lista_vehiculos = cursor.fetchall()
        
        # Traemos los precios disponibles (ej. cajon paso, cajon frecuente)
        cursor.execute("SELECT folio_precio, tipo, precio FROM Precios WHERE tipo = 'cajon'")
        lista_tarifas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('estancias.html', estancias=lista_estancias, vehiculos=lista_vehiculos, tarifas=lista_tarifas)
    except mysql.connector.Error as err:
        flash(f'Error al cargar estancias: {err}', 'error')
        return render_template('estancias.html', estancias=[], vehiculos=[], tarifas=[])


@app.route('/pagos')
@login_required
def pagos():
    # La vista de pagos ahora lee de la tabla Cobros
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.*, s.fecha_salida, u.nombre as cobrador
            FROM Cobros c
            JOIN Servicios s ON c.folio_servicio = s.folio_servicio
            JOIN Usuarios u ON c.usuario_id = u.usuario_id
            ORDER BY s.fecha_salida DESC, c.hora_estancia DESC
        """)
        lista_cobros = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('pagos.html', pagos=lista_cobros)
    except mysql.connector.Error as err:
        flash(f'Error al cargar cobros: {err}', 'error')
        return render_template('pagos.html', pagos=[])

@app.route('/pensiones')
@login_required
def pensiones():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Traemos las pensiones haciendo JOIN para mostrar el nombre del cliente
        cursor.execute("""
            SELECT p.*, c.nombre as nombre_cliente 
            FROM Pensiones p
            JOIN Clientes c ON p.cliente_id = c.cliente_id
        """)
        lista_pensiones = cursor.fetchall()
        
        # Para el formulario de "Nueva Pensión" necesitamos la lista de clientes
        cursor.execute("SELECT cliente_id, nombre FROM Clientes")
        lista_clientes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return render_template('pensiones.html', pensiones=lista_pensiones, clientes=lista_clientes)
    except mysql.connector.Error as err:
        flash(f'Error al cargar pensiones: {err}', 'error')
        return render_template('pensiones.html', pensiones=[], clientes=[])

@app.route('/tarifas')
@login_required
def tarifas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Consultamos la tabla Precios
        cursor.execute("SELECT * FROM Precios")
        lista_precios = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('tarifas.html', tarifas=lista_precios)
    except mysql.connector.Error as err:
        flash(f'Error al cargar tarifas: {err}', 'error')
        return render_template('tarifas.html', tarifas=[])


@app.route('/usuarios')
@admin_required
def usuarios():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Traemos todos los usuarios, pero sin la contraseña por seguridad al mostrar en la vista
        cursor.execute("SELECT usuario_id, nombre, email, username, perfil FROM Usuarios")
        lista_usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('usuarios.html', usuarios=lista_usuarios)
    except mysql.connector.Error as err:
        flash(f'Error al cargar usuarios: {err}', 'error')
        return render_template('usuarios.html', usuarios=[])

@app.route('/reportes')
@admin_required
def reportes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtenemos los ingresos agrupados por fecha (últimos 7 días con actividad)
        cursor.execute("""
            SELECT s.fecha_salida as fecha, SUM(c.monto_total) as total_dia
            FROM Cobros c
            JOIN Servicios s ON c.folio_servicio = s.folio_servicio
            WHERE s.fecha_salida IS NOT NULL
            GROUP BY s.fecha_salida
            ORDER BY s.fecha_salida DESC
            LIMIT 7
        """)
        ingresos_recientes = cursor.fetchall()
        
        # Invertimos la lista para que la gráfica muestre el día más antiguo primero y el más reciente al final
        ingresos_recientes.reverse()
        
        cursor.close()
        conn.close()
        
        return render_template('reportes.html', ingresos=ingresos_recientes)
    except mysql.connector.Error as err:
        flash(f'Error al cargar reportes: {err}', 'error')
        return render_template('reportes.html', ingresos=[])

# ============================================================
# CRUD API — CLIENTES
# ============================================================

@app.route('/api/clientes', methods=['POST'])
@login_required
def api_crear_cliente():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """INSERT INTO Clientes (nombre, telefono, email, rfc, usuario_id)
                   VALUES ( %s, %s, %s, %s, %s)"""
        #obetner el id de usuario logeado y registrando al cliente
        usuario_id = session['user']['usuario_id']
        valores = (
            data.get("nombre", ""),
            data.get("telefono", ""),
            data.get("email", ""),
            data.get("rfc", ""),
            usuario_id)
        cursor.execute(query, valores)
        conn.commit()
        nuevo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Cliente registrado correctamente", "id": nuevo_id})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de DB: {err}"})

@app.route('/api/clientes/<int:id_cliente>', methods=['PUT'])
@login_required
def api_editar_cliente(id_cliente):
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """UPDATE Clientes
                   SET nombre=%s, telefono=%s, email=%s, rfc=%s
                   WHERE cliente_id=%s"""
        valores = (
            data.get("nombre"),
            data.get("telefono"),
            data.get("email"),
            data.get("rfc"),
            id_cliente)
        cursor.execute(query, valores)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Cliente actualizado correctamente"})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de DB: {err}"})

@app.route('/api/clientes/<int:id_cliente>', methods=['DELETE'])
@login_required
def api_eliminar_cliente(id_cliente):
    try: 
        conn = get_db_connection()
        cursor = conn.cursor()

        #Eliminar por llave primaria
        cursor.execute("DELETE FROM Clientes WHERE cliente_id=%s", (id_cliente,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success":True,"message": "Cliente eliminado correctamente"})
    except mysql.connector.Error as err:
        #Si hay vehiculos registrados mysql bloqueara el borrado por llave foranea, hacer un trigger
        return jsonify({"success":False, "message": "No se puede eliminar, cliente con vehiculos registrados"})



# ============================================================
# CRUD API — VEHICULOS
# ============================================================
from flask import request, jsonify
@app.route('/api/vehiculos/crear', methods=['POST'])
@login_required
def api_crear_vehiculo():
    try:
        # 1. Recibimos los datos que mandó app.js
        datos = request.get_json()
        
        matricula = datos.get('matricula')
        marca = datos.get('marca')
        modelo = datos.get('modelo')
        color = datos.get('color')
        id_cliente = datos.get('id_cliente')

        # 2. Conectamos a la BD usando tu función estándar
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Vehiculos (matricula, marca, modelo, color, cliente_id) 
            VALUES (%s, %s, %s, %s, %s)
        """, (matricula, marca, modelo, color, id_cliente))
        
        conn.commit()
        cursor.close()
        conn.close()

        # 3. Respuesta de éxito
        return jsonify({'success': True, 'mensaje': 'Vehículo registrado correctamente'})

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'error': f"Error de BD: {err}"}), 500
    except Exception as e:
        print("Error en /api/vehiculos/crear:", e)
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/vehiculos/<int:matricula>', methods=['PUT'])
@login_required
def api_editar_vehiculo(matricula):
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # No actualizamos la matrícula porque es la llave primaria, solo el resto de los datos
        query = """UPDATE Vehiculos 
                   SET modelo=%s, marca=%s, color=%s, cliente_id=%s 
                   WHERE matricula=%s"""
                   
        valores = (
            data.get("modelo"),
            data.get("marca"),
            data.get("color"),
            data.get("cliente_id"),
            matricula
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Vehículo actualizado correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})


@app.route('/api/vehiculos/<int:matricula>', methods=['DELETE'])
@login_required
def api_eliminar_vehiculo(matricula):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Eliminamos buscando por la matrícula (string)
        cursor.execute("DELETE FROM Vehiculos WHERE matricula=%s", (matricula,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Vehículo eliminado correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": "No se puede eliminar: el vehículo tiene servicios/cobros registrados."})


# ============================================================
# CRUD API — ESTANCIAS
# ============================================================

@app.route('/api/estancias', methods=['POST'])
@login_required
def api_crear_estancia():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtenemos fecha y hora actual separadas
        ahora = datetime.now()
        fecha_ent = ahora.strftime("%Y-%m-%d")
        hora_ent = ahora.strftime("%H:%M:%S")
        
        query = """INSERT INTO Servicios (matricula, fecha_entrada, hora_entrada, folio_precio, tipo_servicio) 
                   VALUES (%s, %s, %s, %s, %s)"""
                   
        valores = (
            data.get("matricula").upper(),
            fecha_ent,
            hora_ent,
            data.get("folio_precio"), # El ID de la tarifa seleccionada
            "cajon"
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": f"Entrada registrada para el vehículo {valores[0]}"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})

@app.route('/api/estancias/<int:folio_servicio>/salida', methods=['POST'])
@login_required
def api_registrar_salida(folio_servicio):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Obtenemos los datos del servicio para saber a qué hora entró
        cursor.execute("""
            SELECT s.*, p.precio 
            FROM Servicios s 
            JOIN Precios p ON s.folio_precio = p.folio_precio 
            WHERE s.folio_servicio = %s AND s.fecha_salida IS NULL
        """, (folio_servicio,))
        servicio = cursor.fetchone()
        
        if not servicio:
            return jsonify({"success": False, "message": "Servicio no encontrado o ya tiene salida."})
            
        # 2. Calculamos la fecha y hora de salida
        ahora = datetime.now()
        fecha_sal = ahora.strftime("%Y-%m-%d")
        hora_sal = ahora.strftime("%H:%M:%S")
        
        str_entrada = f"{servicio['fecha_entrada']} {servicio['hora_entrada']}"
        dt_entrada = datetime.strptime(str_entrada, "%Y-%m-%d %H:%M:%S")
        
        tiempo_estancia = ahora - dt_entrada
        minutos_totales = int(tiempo_estancia.total_seconds() / 60)
        
        # Redondeamos las horas hacia arriba (ej: 65 mins = 2 horas)
        horas_cobrables = math.ceil(minutos_totales / 60)
        if horas_cobrables == 0:
            horas_cobrables = 1 # Cobro mínimo de 1 hora
            
        # --- LÓGICA DE COBRO MATEMÁTICA ---
        # Si tienes una regla específica (ej. después de 5 horas cambia el precio), modifícalo aquí.
        precio_base = float(servicio['precio'])
        monto_total = horas_cobrables * precio_base
        
        # Formateamos el tiempo de estancia como lo pide la BD (HH:MM:SS)
        horas_str = str(minutos_totales // 60).zfill(2)
        minutos_str = str(minutos_totales % 60).zfill(2)
        tiempo_formateado = f"{horas_str}:{minutos_str}:00"
        
        # 3. Actualizamos el servicio poniendo la salida
        cursor.execute("""
            UPDATE Servicios 
            SET fecha_salida = %s, hora_salida = %s 
            WHERE folio_servicio = %s
        """, (fecha_sal, hora_sal, folio_servicio))
        
        # 4. Insertamos el ticket en la tabla Cobros
        usuario_id = session['user']['usuario_id']
        cursor.execute("""
            INSERT INTO Cobros (folio_servicio, matricula, hora_estancia, usuario_id, monto_total) 
            VALUES (%s, %s, %s, %s, %s)
        """, (folio_servicio, servicio['matricula'], tiempo_formateado, usuario_id, monto_total))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Salida exitosa. Tiempo: {horas_str}h {minutos_str}m. Total a cobrar: ${monto_total:.2f}"
        })
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})

# ============================================================
# CRUD API — PENSIONES
# ============================================================

@app.route('/api/pensiones', methods=['POST'])
@login_required
def api_crear_pension():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insertamos la pensión. (Asumiendo columnas: cliente_id, fecha_inicio, fecha_fin, monto, estado)
        query = """INSERT INTO Pensiones (cliente_id, fecha_inicio, fecha_fin, monto, estado) 
                   VALUES (%s, %s, %s, %s, %s)"""
        valores = (
            data.get("cliente_id"),
            data.get("fecha_inicio"),
            data.get("fecha_fin"),
            float(data.get("costo_mensual", 0.0)),
            "ACTIVA"
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Pensión registrada correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})


@app.route('/api/pensiones/<int:pension_id>', methods=['PUT'])
@login_required
def api_editar_pension(pension_id):
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """UPDATE Pensiones 
                   SET fecha_inicio=%s, fecha_fin=%s, monto=%s, estado=%s 
                   WHERE pension_id=%s"""
        valores = (
            data.get("fecha_inicio"),
            data.get("fecha_fin"),
            float(data.get("costo_mensual", 0.0)),
            data.get("estado", "ACTIVA"),
            pension_id
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Pensión actualizada correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})

@app.route('/api/pensiones/<int:pension_id>', methods=['DELETE'])
@login_required
def api_eliminar_pension(pension_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # En lugar de borrar el registro (para no perder el historial), es mejor cambiar el estado a CANCELADA
        cursor.execute("UPDATE Pensiones SET estado='CANCELADA' WHERE pension_id=%s", (pension_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Pensión cancelada correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})

# ============================================================
# CRUD API — TARIFAS
# ============================================================

@app.route('/api/tarifas', methods=['POST'])
@login_required
def api_crear_tarifa():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insertamos el nuevo precio/tarifa
        query = "INSERT INTO Precios (tipo, precio) VALUES (%s, %s)"
        # Extraemos 'tipo' y 'precio' (si en tu JS viejo usabas 'descripcion' y 'costo_inicial', adáptalo aquí)
        valores = (
            data.get("tipo", "cajon"), 
            float(data.get("precio", 0.0))
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Tarifa creada correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})


@app.route('/api/tarifas/<int:folio_precio>', methods=['PUT'])
@login_required
def api_editar_tarifa(folio_precio):
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "UPDATE Precios SET tipo=%s, precio=%s WHERE folio_precio=%s"
        valores = (
            data.get("tipo"), 
            float(data.get("precio", 0.0)), 
            folio_precio
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Tarifa actualizada correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})


# ============================================================
# CRUD API — USUARIOS
# ============================================================

@app.route('/api/usuarios', methods=['POST'])
@admin_required
def api_crear_usuario():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """INSERT INTO Usuarios (nombre, email, username, password, perfil) 
                   VALUES (%s, %s, %s, %s, %s)"""
                   
        valores = (
            data.get("nombre", ""),
            data.get("email", ""),
            data.get("username", ""),
            data.get("password", ""), # En un proyecto real, aquí deberías aplicar un "hash" a la contraseña
            data.get("perfil", "cobrador")
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuario creado correctamente"})
        
    except mysql.connector.Error as err:
        if err.errno == 1062: # Error de MySQL cuando un dato "UNIQUE" ya existe
            return jsonify({"success": False, "message": "Error: El nombre de usuario (username) ya existe."})
        return jsonify({"success": False, "message": f"Error de BD: {err}"})


@app.route('/api/usuarios/<int:usuario_id>', methods=['PUT'])
@admin_required
def api_editar_usuario(usuario_id):
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Si el administrador escribió algo en la contraseña, la actualizamos. Si no, se queda la que ya tenía.
        if data.get("password"):
            query = """UPDATE Usuarios 
                       SET nombre=%s, email=%s, username=%s, password=%s, perfil=%s 
                       WHERE usuario_id=%s"""
            valores = (
                data.get("nombre"),
                data.get("email"),
                data.get("username"),
                data.get("password"),
                data.get("perfil"),
                usuario_id
            )
        else:
            query = """UPDATE Usuarios 
                       SET nombre=%s, email=%s, username=%s, perfil=%s 
                       WHERE usuario_id=%s"""
            valores = (
                data.get("nombre"),
                data.get("email"),
                data.get("username"),
                data.get("perfil"),
                usuario_id
            )
        
        cursor.execute(query, valores)
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuario actualizado correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})


@app.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
@admin_required
def api_eliminar_usuario(usuario_id):
    # Regla de seguridad: Un usuario no puede borrarse a sí mismo si está en sesión
    if usuario_id == session.get('user', {}).get('usuario_id'):
        return jsonify({"success": False, "message": "No puedes eliminar tu propia cuenta mientras estás conectado."})
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Usuarios WHERE usuario_id=%s", (usuario_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({"success": True, "message": "Usuario eliminado correctamente"})
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": "No se puede eliminar: el usuario ya tiene cobros o registros asociados en la base de datos."})


# ============================================================
# STATS API
# ============================================================

@app.route('/api/stats')
@login_required
def api_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Vehículos dentro
        cursor.execute("SELECT COUNT(*) as count FROM Servicios WHERE hora_salida IS NULL")
        vehiculos_dentro = cursor.fetchone()['count']
        
        # 2. Total de clientes registrados
        cursor.execute("SELECT COUNT(*) as count FROM Clientes")
        total_clientes = cursor.fetchone()['count']
        
        # 3. Pensiones Activas
        cursor.execute("SELECT COUNT(*) as count FROM Pensiones WHERE estado = 'ACTIVA'")
        pensiones_activas = cursor.fetchone()['count']
        
        # 4. Ingresos del día de hoy
        hoy = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT SUM(monto_total) as total 
            FROM Cobros c
            JOIN Servicios s ON c.folio_servicio = s.folio_servicio
            WHERE s.fecha_salida = %s
        """, (hoy,))
        ingresos_hoy = cursor.fetchone()['total'] or 0.0

        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "vehiculos_dentro": vehiculos_dentro,
            "total_clientes": total_clientes,
            "pensiones_activas": pensiones_activas,
            "ingresos_hoy": float(ingresos_hoy)
        })
        
    except mysql.connector.Error as err:
        return jsonify({"success": False, "message": f"Error de BD: {err}"})


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
