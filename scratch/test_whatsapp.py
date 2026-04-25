import os
from dotenv import load_dotenv
load_dotenv()

import sys
root = os.getcwd()
# Add root so 'services' package is found
if root not in sys.path:
    sys.path.append(root)
# Add src so 'anip' package is found
src_path = os.path.join(root, 'src')
if src_path not in sys.path:
    sys.path.append(src_path)
# Add services/api so 'app' is found (for disaster_alerts imports)
api_path = os.path.join(root, 'services', 'api')
if api_path not in sys.path:
    sys.path.append(api_path)

from anip.shared.database import get_db_session
from anip.shared.models.social import User, UserSettings, DisasterAlert
from anip.shared.notifications import notifier
from app.disaster_alerts import process_article_for_alerts
from anip.shared.models.news import NewsArticle

def test_whatsapp_option():
    with get_db_session() as db:
        # 1. Create a test user if not exists
        username = "test_whatsapp_user"
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(
                username=username,
                email="test_whatsapp@example.com",
                password_hash="fake_hash",
                phone_number="+916379138735" # Using the one from .env for testing
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created user: {username}")
        else:
            user.phone_number = "+916379138735"
            db.commit()
            print(f"User {username} already exists")

        # 2. Check if settings were automatically updated
        settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
        if not settings:
            # This should have been handled by my model default change, 
            # but let's see what happens if we manually trigger the profile update logic
            from services.api.app.advanced_social import update_profile, ProfileUpdate
            # We simulate the API call logic
            update = ProfileUpdate(phone_number="+916379138735")
            # Manually run the logic I added to update_profile
            if update.phone_number.strip():
                settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
                if not settings:
                    settings = UserSettings(user_id=user.id, whatsapp_notifications=True)
                    db.add(settings)
                else:
                    settings.whatsapp_notifications = True
                db.commit()
                db.refresh(settings)
        
        print(f"WhatsApp notifications enabled for {username}: {settings.whatsapp_notifications}")

        # 3. Create a mock disaster article
        article = NewsArticle(
            title="CRITICAL: Major Earthquake Hits Downtown",
            content="A magnitude 8.5 earthquake has struck the city center. Casualties are high. Evacuation is required immediately.",
            source="Test News"
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        print(f"Created disaster article: {article.id}")

        # 4. Trigger alert processing (this should trigger WhatsApp broadcast)
        print("Processing article for alerts...")
        # Since process_article_for_alerts is async, we need to run it in a loop if needed, 
        # but here we can just call it if we use a sync wrapper or just test the logic inside.
        
        # Actually, let's just manually trigger the broadcast part to see if it sends
        whatsapp_msg = f"🚨 TEST ALERT: {article.title}"
        count = notifier.broadcast_alert(db, whatsapp_msg)
        print(f"WhatsApp broadcast sent to {count} users.")

if __name__ == "__main__":
    test_whatsapp_option()
