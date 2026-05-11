import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'estacionamiento_db')
}

def setup_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Disable foreign key checks to drop tables
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        tables_to_drop = ['PAGO', 'ESTANCIA', 'TARIFA', 'PENSION', 'VEHICULO', 'CLIENTE', 'USUARIO']
        
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
            ) ENGINE=InnoDB;
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
            ) ENGINE=InnoDB;
        """)

        # 3. VEHICULO
        cursor.execute("""
            CREATE TABLE VEHICULO (
                id_vehiculo INT AUTO_INCREMENT PRIMARY KEY,
                placa VARCHAR(20) UNIQUE,
                marca VARCHAR(50),
                modelo VARCHAR(50),
                color VARCHAR(30),
                estado ENUM('ACTIVO', 'INACTIVO') DEFAULT 'ACTIVO',
                id_cliente INT,
                FOREIGN KEY (id_cliente) REFERENCES CLIENTE(id_cliente) ON DELETE CASCADE
            ) ENGINE=InnoDB;
        """)

        # 4. TARIFA
        cursor.execute("""
            CREATE TABLE TARIFA (
                id_tarifa INT AUTO_INCREMENT PRIMARY KEY,
                descripcion VARCHAR(100),
                costo_hora DECIMAL(10,2),
                horas_limite_reduccion INT,
                costo_hora_reducida DECIMAL(10,2),
                tipo_cliente_aplicable ENUM('REGISTRADO', 'OCASIONAL', 'AMBOS') DEFAULT 'AMBOS',
                estado ENUM('ACTIVA', 'INACTIVA') DEFAULT 'ACTIVA',
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
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
            ) ENGINE=InnoDB;
        """)

        # 6. PENSION
        cursor.execute("""
            CREATE TABLE PENSION (
                id_pension INT AUTO_INCREMENT PRIMARY KEY,
                id_cliente INT,
                id_vehiculo INT NULL,
                fecha_inicio DATE,
                fecha_fin DATE,
                costo_mensual DECIMAL(10,2),
                estado ENUM('ACTIVA', 'INACTIVA', 'CANCELADA') DEFAULT 'ACTIVA',
                observaciones VARCHAR(255) NULL,
                FOREIGN KEY (id_cliente) REFERENCES CLIENTE(id_cliente) ON DELETE CASCADE,
                FOREIGN KEY (id_vehiculo) REFERENCES VEHICULO(id_vehiculo) ON DELETE CASCADE
            ) ENGINE=InnoDB;
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
            ) ENGINE=InnoDB;
        """)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # Triggers
        cursor.execute("DROP TRIGGER IF EXISTS trg_cliente_baja_vehiculos;")
        cursor.execute("""
            CREATE TRIGGER trg_cliente_baja_vehiculos
            AFTER UPDATE ON CLIENTE
            FOR EACH ROW
            BEGIN
                IF NEW.estado = 'INACTIVO' AND OLD.estado = 'ACTIVO' THEN
                    UPDATE VEHICULO SET estado = 'INACTIVO' WHERE id_cliente = NEW.id_cliente;
                END IF;
            END;
        """)

        # Insert Default Admin and basic Tariff
        hashed_pwd = generate_password_hash('admin')
        cursor.execute("""
            INSERT INTO USUARIO (nombre, email, username, password, perfil)
            VALUES ('Administrador', 'admin@example.com', 'admin', %s, 'admin')
        """, (hashed_pwd,))
        
        cursor.execute("""
            INSERT INTO TARIFA (descripcion, costo_hora, horas_limite_reduccion, costo_hora_reducida, tipo_cliente_aplicable)
            VALUES ('Público General', 30.00, 5, 25.00, 'OCASIONAL')
        """)
        
        cursor.execute("""
            INSERT INTO TARIFA (descripcion, costo_hora, horas_limite_reduccion, costo_hora_reducida, tipo_cliente_aplicable)
            VALUES ('Cliente Frecuente', 26.00, 5, 22.00, 'REGISTRADO')
        """)
        
        cursor.execute("""
            INSERT INTO TARIFA (descripcion, costo_hora, horas_limite_reduccion, costo_hora_reducida, tipo_cliente_aplicable)
            VALUES ('Pensión Mensual', 0, 0, 0, 'AMBOS')
        """)

        conn.commit()
        print("Database structure successfully created with sample data.")

        # Import and run seed data
        import seed_data
        print("Running seed_data script...")
        seed_data.seed_database()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    setup_database()
