import os
import sys
import bcrypt

# Add paths
sys.path.insert(0, os.path.abspath('src'))
sys.path.insert(0, os.path.abspath('services/api'))

# Set env vars to match .env
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = ''
os.environ['POSTGRES_HOST'] = '127.0.0.1'
os.environ['POSTGRES_PORT'] = '5432'

from anip.shared.database import get_db_session
from anip.shared.models.social import User

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def reset_password(username_or_email, new_password):
    with get_db_session() as db:
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        if not user:
            print(f"User {username_or_email} not found.")
            return
        
        user.password_hash = get_password_hash(new_password)
        db.commit()
        print(f"Password for {user.username} has been reset to: {new_password}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reset_password.py <username/email> <new_password>")
    else:
        reset_password(sys.argv[1], sys.argv[2])
