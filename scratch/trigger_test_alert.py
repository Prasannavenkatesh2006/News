import os
import sys
import asyncio

# Add paths
sys.path.insert(0, os.path.abspath('src'))
sys.path.insert(0, os.path.abspath('services/api'))

# Set env vars
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = ''
os.environ['POSTGRES_HOST'] = '127.0.0.1'
os.environ['POSTGRES_PORT'] = '5432'

from dotenv import load_dotenv
load_dotenv()

from anip.shared.database import get_db_session
from anip.shared.models.news import NewsArticle
from anip.shared.notifications import notifier
from sqlalchemy.orm import Session

async def manual_broadcast():
    print("CHECK: Twilio Config...")
    print(f"  SID: {notifier.account_sid[:8]}...")
    print(f"  From: {notifier.from_number}")
    print(f"  Enabled: {notifier.enabled}")

    with get_db_session() as db:
        msg = "🚨 PULSE TEST ALERT: If you see this, WhatsApp is working! 🚨"
        print(f"BROADCAST: Sending to all opted-in users...")
        
        # Manually call broadcast_alert to see the result
        count = notifier.broadcast_alert(db, msg)
        print(f"RESULT: Successfully sent to {count} users.")
        
        if count == 0:
            print("WARNING: No messages were sent. This could be because:")
            print("1. No users have a phone number starting with '+'")
            print("2. No users have WhatsApp notifications toggled ON")
            print("3. Twilio API rejected the requests (check Twilio Dashboard)")

if __name__ == "__main__":
    asyncio.run(manual_broadcast())
