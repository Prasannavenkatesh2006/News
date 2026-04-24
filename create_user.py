import psycopg2

try:
    conn = psycopg2.connect(
        host='127.0.0.1', 
        database='postgres', 
        user='postgres', 
        password='3006', 
        port='5432'
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check if user exists first
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname='anip'")
    if not cur.fetchone():
        cur.execute("CREATE USER anip WITH PASSWORD '3006';")
        print("User 'anip' created.")
    else:
        print("User 'anip' already exists.")
        
    cur.execute("GRANT ALL PRIVILEGES ON DATABASE anip TO anip;")
    # Also grant on public schema
    cur.close()
    conn.close()
    
    # Connect to anip db as postgres to grant schema permissions
    conn = psycopg2.connect(
        host='127.0.0.1', 
        database='anip', 
        user='postgres', 
        password='3006', 
        port='5432'
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("GRANT ALL ON SCHEMA public TO anip;")
    print("Permissions granted on 'anip' database.")
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
