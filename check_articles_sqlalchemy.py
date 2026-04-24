import os
import sys
sys.path.insert(0, os.path.abspath('src'))
os.chdir('C:\Users\bpras\Downloads\Pulse---ANIP-main\Pulse---ANIP-main')

from anip.config import settings
settings.database.host = 'localhost'

from anip.shared.database import get_db_session
from anip.shared.models.news import NewsArticle

try:
    with get_db_session() as db:
        count = db.query(NewsArticle).count()
        print(f"NewsArticle count: {count}")
        if count > 0:
            latest = db.query(NewsArticle).order_by(NewsArticle.created_at.desc()).first()
            print(f"Latest title: {latest.title}")
            print(f"  Country: {latest.country}, State: {latest.state}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
