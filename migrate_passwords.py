import mysql.connector
from werkzeug.security import generate_password_hash

conn = mysql.connector.connect(host='localhost', user='root', password='', database='estacionamiento_db')
cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT id_usuario, username, password FROM USUARIO')
users = cursor.fetchall()
updated = 0
for u in users:
    pw = u['password']
    # Only hash if not already hashed (werkzeug hashes start with algorithm prefix)
    if not pw.startswith('scrypt:') and not pw.startswith('pbkdf2:'):
        hashed = generate_password_hash(pw)
        cursor.execute('UPDATE USUARIO SET password=%s WHERE id_usuario=%s', (hashed, u['id_usuario']))
        updated += 1
        print(f"Migrated user: {u['username']}")

conn.commit()
cursor.close()
conn.close()
print(f"Done. {updated} passwords migrated to hash.")
