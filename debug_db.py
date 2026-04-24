import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env')

try:
    conn = psycopg2.connect(
        host="localhost",
        database="anip",
        user="anip",
        password="3006",
        port="5432"
    )
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM newsarticle;")
    print(f"NewsArticle Count: {cur.fetchone()[0]}")
    
    cur.execute("SELECT title, country, state, api_source FROM newsarticle ORDER BY created_at DESC LIMIT 10;")
    print("Latest articles in newsarticle table:")
    for row in cur.fetchall():
        print(f"Title: {row[0]}")
        print(f"  Country: {row[1]}, State: {row[2]}, Platform: {row[3]}")
        
    cur.execute("SELECT COUNT(*) FROM posts;")
    print(f"Posts Count: {cur.fetchone()[0]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
