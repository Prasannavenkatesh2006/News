import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))
from anip.shared.database import get_db_session
from anip.shared.models.social import User

with get_db_session() as db:
    users = db.query(User).all()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Phone: {user.phone_number}")
