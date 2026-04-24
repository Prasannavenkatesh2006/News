import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="anip",
        user="anip",
        password="3006",
        port="5432"
    )
    cur = conn.cursor()
    
    print("Checking tables...")
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = cur.fetchall()
    for t in tables:
        print(f"Table: {t[0]}")
        cur.execute(f"SELECT COUNT(*) FROM {t[0]};")
        count = cur.fetchone()[0]
        print(f"  Count: {count}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
