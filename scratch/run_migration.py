import os
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from anip.shared.database import SessionLocal, engine

def run_migration():
    migration_path = "migrations/add_whatsapp_columns.sql"
    if not os.path.exists(migration_path):
        print(f"Migration file not found: {migration_path}")
        return

    with open(migration_path, "r") as f:
        sql = f.read()

    with engine.connect() as conn:
        print("Running migration...")
        for statement in sql.split(";"):
            if statement.strip():
                try:
                    conn.execute(text(statement))
                    conn.commit()
                    print(f"Executed: {statement.strip()[:50]}...")
                except Exception as e:
                    print(f"Error executing statement: {e}")

if __name__ == "__main__":
    run_migration()
