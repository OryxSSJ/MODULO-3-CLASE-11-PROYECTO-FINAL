import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'estacionamiento_db'
}

def setup_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Disable foreign key checks to drop tables
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        tables_to_drop = ['Cobros', 'Servicios', 'Precios', 'Pensiones', 'Vehiculos', 'Clientes', 'Usuarios',
                          'PAGO', 'ESTANCIA', 'TARIFA', 'PENSION', 'VEHICULO', 'CLIENTE', 'USUARIO']
        
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")

        # 1. USUARIO (Required for login)
        cursor.execute("""
            CREATE TABLE USUARIO (
                id_usuario INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(50),
                email VARCHAR(100),
                username VARCHAR(50) UNIQUE,
                password VARCHAR(255),
                perfil ENUM('admin', 'cobrador')
            );
        """)

        # 2. CLIENTE
        cursor.execute("""
            CREATE TABLE CLIENTE (
                id_cliente INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100),
                telefono VARCHAR(20),
                tipo_cliente ENUM('REGISTRADO', 'OCASIONAL'),
                fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                estado ENUM('ACTIVO', 'INACTIVO') DEFAULT 'ACTIVO'
            );
        """)

        # 3. VEHICULO
        cursor.execute("""
            CREATE TABLE VEHICULO (
                id_vehiculo INT AUTO_INCREMENT PRIMARY KEY,
                placa VARCHAR(20) UNIQUE,
                marca VARCHAR(50),
                modelo VARCHAR(50),
                color VARCHAR(30),
                id_cliente INT,
                FOREIGN KEY (id_cliente) REFERENCES CLIENTE(id_cliente) ON DELETE SET NULL
            );
        """)

        # 4. TARIFA
        cursor.execute("""
            CREATE TABLE TARIFA (
                id_tarifa INT AUTO_INCREMENT PRIMARY KEY,
                descripcion VARCHAR(100),
                tiempo_inicial_min INT,
                costo_inicial DECIMAL(10,2),
                costo_por_min_extra DECIMAL(10,4),
                estado ENUM('ACTIVA', 'INACTIVA') DEFAULT 'ACTIVA',
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. ESTANCIA
        cursor.execute("""
            CREATE TABLE ESTANCIA (
                id_estancia INT AUTO_INCREMENT PRIMARY KEY,
                id_vehiculo INT,
                fecha_entrada DATETIME,
                fecha_salida DATETIME NULL,
                id_tarifa INT,
                es_pension BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (id_vehiculo) REFERENCES VEHICULO(id_vehiculo) ON DELETE CASCADE,
                FOREIGN KEY (id_tarifa) REFERENCES TARIFA(id_tarifa) ON DELETE SET NULL
            );
        """)

        # 6. PENSION
        cursor.execute("""
            CREATE TABLE PENSION (
                id_pension INT AUTO_INCREMENT PRIMARY KEY,
                id_cliente INT,
                fecha_inicio DATE,
                fecha_fin DATE,
                costo_mensual DECIMAL(10,2),
                estado ENUM('ACTIVA', 'INACTIVA', 'CANCELADA') DEFAULT 'ACTIVA',
                observaciones VARCHAR(255) NULL,
                FOREIGN KEY (id_cliente) REFERENCES CLIENTE(id_cliente) ON DELETE CASCADE
            );
        """)

        # 7. PAGO
        cursor.execute("""
            CREATE TABLE PAGO (
                id_pago INT AUTO_INCREMENT PRIMARY KEY,
                id_estancia INT NULL,
                id_pension INT NULL,
                monto DECIMAL(10,2),
                fecha_pago DATETIME,
                metodo_pago ENUM('EFECTIVO', 'TARJETA', 'TRANSFERENCIA', 'OTRO'),
                referencia VARCHAR(100) NULL,
                observaciones VARCHAR(255) NULL,
                FOREIGN KEY (id_estancia) REFERENCES ESTANCIA(id_estancia) ON DELETE SET NULL,
                FOREIGN KEY (id_pension) REFERENCES PENSION(id_pension) ON DELETE SET NULL
            );
        """)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # Insert Default Admin and basic Tariff
        cursor.execute("""
            INSERT INTO USUARIO (nombre, email, username, password, perfil)
            VALUES ('Administrador', 'admin@example.com', 'admin', 'admin', 'admin')
        """)
        
        cursor.execute("""
            INSERT INTO TARIFA (descripcion, tiempo_inicial_min, costo_inicial, costo_por_min_extra)
            VALUES ('Tarifa General', 60, 30.00, 0.50)
        """)
        
        cursor.execute("""
            INSERT INTO TARIFA (descripcion, tiempo_inicial_min, costo_inicial, costo_por_min_extra)
            VALUES ('Pensión Mensual', 0, 0, 0)
        """)

        conn.commit()
        print("Database structure successfully created with sample data.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    setup_database()
