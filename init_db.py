import os
import sys
sys.path.insert(0, os.path.abspath('src'))
sys.path.insert(0, os.path.abspath('services/api'))

os.environ.setdefault('POSTGRES_HOST', '127.0.0.1')
os.environ.setdefault('POSTGRES_PORT', '5433')
os.environ.setdefault('POSTGRES_USER', 'anip')
os.environ.setdefault('POSTGRES_PASSWORD', 'anip')
os.environ.setdefault('POSTGRES_DB', 'anip')
os.environ.setdefault('OPENAI_API_KEY', 'sk-dummy')

from anip.shared.database import Base, engine
from anip.shared.models.social import User, Community, Post, Comment, Vote, Notification, Bookmark, DisasterAlert, UserSettings
from anip.shared.models.news import NewsArticle
from sqlalchemy import text

print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")

# Grant all table permissions to 'anip' user in case postgres created them
print("Granting table permissions to 'anip' user...")
try:
    import psycopg2
    conn = psycopg2.connect(host='127.0.0.1', database='anip', user='postgres', password='anip', port='5433')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO anip;")
    cur.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anip;")
    cur.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anip;")
    cur.close()
    conn.close()
    print("Permissions granted.")
except Exception as e:
    print(f"Permission grant failed (may be OK): {e}")

from scripts.seed_communities import seed_communities
seed_communities()
