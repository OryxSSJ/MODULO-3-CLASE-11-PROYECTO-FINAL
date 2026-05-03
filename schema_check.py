import mysql.connector
import json

DB_CONFIG ={
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'estacionamiento_db'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

schema = {}
for table in tables:
    table_name = table[0]
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    schema[table_name] = [{"Field": c[0], "Type": c[1]} for c in columns]

print(json.dumps(schema, indent=2))
cursor.close()
conn.close()
