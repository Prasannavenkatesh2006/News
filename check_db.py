import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath('src'))
# Ensure we are in the right directory for .env
os.chdir('C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main')

from anip.config import settings
# Override host for local check
settings.database.host = 'localhost'

from anip.shared.database import get_db_session
from anip.shared.models.news import NewsArticle
from anip.shared.models.social import Post

try:
    with get_db_session() as db:
        articles = db.query(NewsArticle).count()
        posts = db.query(Post).count()
        print(f"Articles: {articles}")
        print(f"Posts: {posts}")
        
        # Check for India/TN articles
        tn_articles = db.query(NewsArticle).filter(NewsArticle.state == 'Tamil Nadu').count()
        india_articles = db.query(NewsArticle).filter(NewsArticle.country == 'India').count()
        print(f"Tamil Nadu Articles: {tn_articles}")
        print(f"India Articles: {india_articles}")
        
        # Check latest posts
        latest_posts = db.query(Post).order_by(Post.created_at.desc()).limit(5).all()
        print("\nLatest 5 Posts:")
        for p in latest_posts:
            print(f"- {p.title} (Type: {p.post_type}, ID: {p.id})")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
