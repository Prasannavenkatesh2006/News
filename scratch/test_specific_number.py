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

from anip.shared.notifications import notifier

async def direct_test():
    target = "+919600617660"
    msg = "🚨 PULSE PRIVATE TEST: This is a direct test for number 9600617660. 🚨"
    
    print(f"DEBUG: Attempting direct send to {target}...")
    try:
        # send_message returns True/False
        success = notifier.send_message(target, msg)
        if success:
            print(f"SUCCESS: Twilio accepted the message for {target}")
            print("If you still don't see it, CHECK if this phone sent 'join provide-near' to the Twilio number.")
        else:
            print(f"FAILED: Notifier returned False. Check logs for Twilio error.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(direct_test())
