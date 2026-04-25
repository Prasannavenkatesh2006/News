from anip.shared.database import get_db_session
from anip.shared.models.social import DisasterAlert

with get_db_session() as db:
    a = db.query(DisasterAlert).order_by(DisasterAlert.created_at.desc()).first()
    if a:
        print(f"Latest Alert Title: {a.title.encode('ascii', 'ignore').decode()}")
        print(f"Severity: {a.severity}")
        print(f"Created At: {a.created_at}")
    else:
        print("No alerts found.")
