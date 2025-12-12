# inspect_db.py
import os, sqlite3

DB = os.path.join(os.path.dirname(__file__), "app.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("Archivo DB:", DB)
print("\nTablas:")
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
for t in tables:
    print(" -", t)
print("\nColumnas por tabla:")
for t in tables:
    cols = [(r[1], r[2]) for r in cur.execute(f"PRAGMA table_info({t})")]
    print(f" {t}: {cols}")
conn.close()
