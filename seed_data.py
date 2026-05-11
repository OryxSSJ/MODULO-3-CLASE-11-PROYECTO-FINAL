import mysql.connector
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'estacionamiento_db')
}

def seed_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("Iniciando la generación de datos de prueba...")

        # 1. Crear Clientes
        nombres = ['Juan Pérez', 'María Gómez', 'Carlos López', 'Ana Martínez', 'Luis Rodríguez', 
                   'Elena Sánchez', 'Roberto Fernández', 'Laura Torres', 'Diego Ramírez', 'Carmen Flores']
        
        clientes_ids = []
        for i, nombre in enumerate(nombres):
            tipo = 'REGISTRADO' if i % 2 == 0 else 'OCASIONAL'
            tel = f'55{random.randint(10000000, 99999999)}'
            fecha_reg = datetime.now() - timedelta(days=random.randint(100, 700))
            
            cursor.execute("""
                INSERT INTO CLIENTE (nombre, telefono, tipo_cliente, fecha_registro) 
                VALUES (%s, %s, %s, %s)
            """, (nombre, tel, tipo, fecha_reg))
            clientes_ids.append(cursor.lastrowid)
            
        print(f"Creados {len(clientes_ids)} clientes.")

        # 2. Crear Vehículos
        marcas_modelos = [('Toyota', 'Corolla'), ('Nissan', 'Versa'), ('Honda', 'Civic'), 
                          ('Volkswagen', 'Jetta'), ('Mazda', '3'), ('Kia', 'Forte'),
                          ('Chevrolet', 'Aveo'), ('Ford', 'Figo'), ('Hyundai', 'Elantra')]
        colores = ['Rojo', 'Azul', 'Blanco', 'Negro', 'Gris', 'Plata']
        
        vehiculos_ids = []
        for i in range(15):
            marca, modelo = random.choice(marcas_modelos)
            color = random.choice(colores)
            placa = f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}-{random.randint(100, 999)}"
            id_cliente = random.choice(clientes_ids) if random.random() > 0.3 else None
            
            cursor.execute("""
                INSERT INTO VEHICULO (placa, marca, modelo, color, id_cliente) 
                VALUES (%s, %s, %s, %s, %s)
            """, (placa, marca, modelo, color, id_cliente))
            vehiculos_ids.append(cursor.lastrowid)
            
        print(f"Creados {len(vehiculos_ids)} vehículos.")

        # Obtener tarifas (para usarlas en estancias)
        cursor.execute("SELECT * FROM TARIFA")
        tarifas = cursor.fetchall()
        tarifa_ocasional = next((t for t in tarifas if t['tipo_cliente_aplicable'] == 'OCASIONAL'), tarifas[0])
        tarifa_registrado = next((t for t in tarifas if t['tipo_cliente_aplicable'] == 'REGISTRADO'), tarifas[0])

        # 3. Crear Estancias y Pagos (distribuidos en el año actual)
        año_actual = datetime.now().year
        mes_actual = datetime.now().month
        
        total_estancias = 0
        for mes in range(1, mes_actual + 1):
            # Generar más estancias en algunos meses para que la gráfica varíe
            num_estancias_mes = random.randint(15, 40)
            
            for _ in range(num_estancias_mes):
                dia = random.randint(1, 28)
                hora_entrada = random.randint(7, 20) # Entre 7 AM y 8 PM
                minuto_entrada = random.randint(0, 59)
                
                fecha_ent = datetime(año_actual, mes, dia, hora_entrada, minuto_entrada)
                
                # Duración aleatoria entre 30 mins y 8 horas
                duracion_mins = random.randint(30, 480)
                fecha_sal = fecha_ent + timedelta(minutes=duracion_mins)
                
                # Evitar que la fecha de salida sea en el futuro si es el mes/día actual
                if fecha_sal > datetime.now():
                    fecha_sal = None
                
                id_vehiculo = random.choice(vehiculos_ids)
                
                # Asignar tarifa
                tarifa = tarifa_ocasional
                cursor.execute("SELECT id_cliente FROM VEHICULO WHERE id_vehiculo = %s", (id_vehiculo,))
                v = cursor.fetchone()
                if v and v['id_cliente']:
                    cursor.execute("SELECT tipo_cliente FROM CLIENTE WHERE id_cliente = %s", (v['id_cliente'],))
                    c = cursor.fetchone()
                    if c and c['tipo_cliente'] == 'REGISTRADO':
                        tarifa = tarifa_registrado
                        
                cursor.execute("""
                    INSERT INTO ESTANCIA (id_vehiculo, fecha_entrada, fecha_salida, id_tarifa) 
                    VALUES (%s, %s, %s, %s)
                """, (id_vehiculo, fecha_ent, fecha_sal, tarifa['id_tarifa']))
                id_estancia = cursor.lastrowid
                total_estancias += 1
                
                # Si salió, generar pago
                if fecha_sal:
                    horas = max(1, -(-duracion_mins // 60)) # Ceil division
                    tarifa_base = float(tarifa['costo_hora'])
                    horas_limite = int(tarifa['horas_limite_reduccion'])
                    tarifa_reducida = float(tarifa['costo_hora_reducida'])
                    
                    if horas <= horas_limite or horas_limite == 0:
                        monto = horas * tarifa_base
                    else:
                        monto = (horas_limite * tarifa_base) + ((horas - horas_limite) * tarifa_reducida)
                        
                    metodo_pago = random.choice(['EFECTIVO', 'TARJETA', 'EFECTIVO', 'EFECTIVO']) # Más efectivo
                    
                    cursor.execute("""
                        INSERT INTO PAGO (id_estancia, monto, fecha_pago, metodo_pago) 
                        VALUES (%s, %s, %s, %s)
                    """, (id_estancia, monto, fecha_sal, metodo_pago))
                    
        print(f"Creadas {total_estancias} estancias con sus respectivos pagos.")

        # 4. Crear Pensiones
        clientes_registrados = [c for c in clientes_ids if random.random() > 0.5][:4] # Tomar algunos
        
        for id_cli in clientes_registrados:
            # Buscar un vehículo de este cliente
            cursor.execute("SELECT id_vehiculo FROM VEHICULO WHERE id_cliente = %s LIMIT 1", (id_cli,))
            veh = cursor.fetchone()
            id_veh = veh['id_vehiculo'] if veh else None
            
            # Pensión de los últimos 2 meses o activa
            mes_inicio = max(1, mes_actual - random.randint(0, 2))
            fecha_inicio = datetime(año_actual, mes_inicio, 1).date()
            fecha_fin = (datetime(año_actual, mes_inicio, 1) + timedelta(days=60)).date()
            
            estado = 'ACTIVA' if fecha_fin > datetime.now().date() else 'INACTIVA'
            costo = 1500.00
            
            cursor.execute("""
                INSERT INTO PENSION (id_cliente, id_vehiculo, fecha_inicio, fecha_fin, costo_mensual, estado) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_cli, id_veh, fecha_inicio, fecha_fin, costo, estado))
            id_pension = cursor.lastrowid
            
            # Pagos de la pensión
            meses_pagados = 1 if estado == 'ACTIVA' else 2
            for m in range(meses_pagados):
                fecha_pago_pension = datetime(año_actual, mes_inicio + m, 2)
                cursor.execute("""
                    INSERT INTO PAGO (id_pension, monto, fecha_pago, metodo_pago) 
                    VALUES (%s, %s, %s, %s)
                """, (id_pension, costo, fecha_pago_pension, 'TRANSFERENCIA'))

        print("Pensiones creadas con éxito.")

        conn.commit()
        print("¡Datos de prueba generados correctamente!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    seed_database()
