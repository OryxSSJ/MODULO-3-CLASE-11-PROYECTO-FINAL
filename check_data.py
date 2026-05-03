import mysql.connector
import json

DB_CONFIG ={
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'estacionamiento_db'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT * FROM Precios")
print("Precios:", cursor.fetchall())

cursor.execute("SELECT * FROM Clientes LIMIT 2")
print("Clientes:", cursor.fetchall())

cursor.close()
conn.close()
