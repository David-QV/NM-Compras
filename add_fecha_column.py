# add_fecha_column.py
import os, sqlite3

DB = os.path.join(os.path.dirname(__file__), "app.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Ver columnas actuales
cols = [r[1] for r in cur.execute("PRAGMA table_info(requerimientos)")]
print("Columnas actuales:", cols)

if "fecha" not in cols:
    # TEXT con default date('now') (SQLite guarda 'YYYY-MM-DD')
    cur.execute("ALTER TABLE requerimientos ADD COLUMN fecha TEXT NOT NULL DEFAULT (date('now'));")
    conn.commit()
    print("Columna 'fecha' agregada.")
else:
    print("La columna 'fecha' ya existe, no se hace nada.")

# Asegura que filas viejas tengan fecha
cur.execute("UPDATE requerimientos SET fecha = date('now') WHERE fecha IS NULL OR fecha = '';")
conn.commit()

conn.close()
print("Listo.")
