import os
import sys
import uuid
import bcrypt

# Add paths
sys.path.insert(0, os.path.abspath('src'))
sys.path.insert(0, os.path.abspath('services/api'))

# Set env vars to match .env (important!)
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = ''
os.environ['POSTGRES_HOST'] = '127.0.0.1'
os.environ['POSTGRES_PORT'] = '5432'

from anip.shared.database import get_db_session
from anip.shared.models.social import User, UserSettings

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_user(username, email, password):
    with get_db_session() as db:
        # Check if exists
        existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing:
            print(f"User {username} already exists, updating password...")
            existing.password_hash = get_password_hash(password)
            db.commit()
            print("Password updated.")
            return
        
        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        print(f"User {username} created successfully with password {password}")

if __name__ == "__main__":
    create_user("testuser", "test@example.com", "password123")
