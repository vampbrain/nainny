import os
import sqlite3
import json

DB_PATH = os.getenv('DB_PATH', 'narrative_intelligence.db')

result = {'db_path': DB_PATH, 'exists': False, 'tables': [], 'size': None}

if not os.path.exists(DB_PATH):
    print(json.dumps(result, indent=2))
    raise SystemExit(0)

result['exists'] = True
result['size'] = os.path.getsize(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%';")
rows = cur.fetchall()
for name, typ in rows:
    try:
        cur.execute(f"SELECT COUNT(*) FROM \"{name}\"")
        cnt = cur.fetchone()[0]
    except Exception as e:
        cnt = str(e)
    result['tables'].append({'name': name, 'type': typ, 'count': cnt})

conn.close()
print(json.dumps(result, indent=2))
