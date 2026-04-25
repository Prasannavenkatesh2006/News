import bcrypt
from anip.shared.database import get_db_session
from anip.shared.models.social import User

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"Error verifying: {e}")
        return False

def check_user_password(username_or_email, password):
    with get_db_session() as db:
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        if not user:
            print(f"User {username_or_email} not found")
            return
        
        print(f"Found user: {user.username}")
        is_valid = verify_password(password, user.password_hash)
        print(f"Password valid: {is_valid}")

if __name__ == "__main__":
    # Test with one of the users
    import sys
    if len(sys.argv) > 2:
        check_user_password(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python test_login_logic.py <username/email> <password>")
