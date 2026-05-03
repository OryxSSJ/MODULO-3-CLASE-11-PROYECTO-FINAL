import mysql.connector
DB_CONFIG ={
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'estacionamiento_db'
}
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, p.precio, c.tipo as tipo_cliente 
        FROM Servicios s 
        LEFT JOIN Precios p ON s.folio_precio = p.folio_precio
        LEFT JOIN Vehiculos v ON s.matricula = v.matricula
        LEFT JOIN Clientes c ON v.cliente_id = c.cliente_id
        LIMIT 1
    """)
    res = cursor.fetchone()
    print("Query success:", res)
except Exception as e:
    print("Error:", e)
