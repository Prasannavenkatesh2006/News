from anip.shared.database import get_db_session
from anip.shared.models.social import User, UserSettings

def list_users():
    try:
        with get_db_session() as db:
            users = db.query(User).all()
            print(f"Found {len(users)} users:")
            for u in users:
                settings = db.query(UserSettings).filter(UserSettings.user_id == u.id).first()
                wa = settings.whatsapp_notifications if settings else "N/A"
                print(f"Username: {u.username}, Phone: {u.phone_number}, WhatsApp: {wa}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_users()
