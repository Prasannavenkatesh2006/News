import os
import sys
import psycopg2

# Direct connection to verify
try:
    conn = psycopg2.connect(
        host="localhost",
        database="anip",
        user="anip",
        password="3006",
        port="5432"
    )
    cur = conn.cursor()
    
    cur.execute("SELECT count(*) FROM news_articles;")
    articles = cur.fetchone()[0]
    
    cur.execute("SELECT count(*) FROM posts;")
    posts = cur.fetchone()[0]
    
    cur.execute("SELECT count(*) FROM news_articles WHERE state = 'Tamil Nadu';")
    tn_articles = cur.fetchone()[0]
    
    cur.execute("SELECT count(*) FROM news_articles WHERE country = 'India';")
    india_articles = cur.fetchone()[0]
    
    print(f"Articles: {articles}")
    print(f"Posts: {posts}")
    print(f"Tamil Nadu Articles: {tn_articles}")
    print(f"India Articles: {india_articles}")
    
    print("\nLatest 5 Posts:")
    cur.execute("SELECT title, post_type FROM posts ORDER BY created_at DESC LIMIT 5;")
    for row in cur.fetchall():
        print(f"- {row[0]} (Type: {row[1]})")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
