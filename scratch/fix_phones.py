from anip.shared.database import get_db_session
from anip.shared.models.social import User

def fix_phones():
    with get_db_session() as db:
        users = db.query(User).all()
        count = 0
        for u in users:
            if u.phone_number and not u.phone_number.startswith('+'):
                if len(u.phone_number) == 10:
                    u.phone_number = "+91" + u.phone_number
                    count += 1
                elif u.phone_number.startswith('91') and len(u.phone_number) == 12:
                    u.phone_number = "+" + u.phone_number
                    count += 1
        db.commit()
        print(f"Fixed {count} phone numbers.")

if __name__ == "__main__":
    fix_phones()
