import os
import logging
from typing import List, Optional
from twilio.rest import Client
from sqlalchemy.orm import Session
from anip.shared.models.social import User, UserSettings

logger = logging.getLogger(__name__)

class WhatsAppNotifier:
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")
        
        self.enabled = bool(self.account_sid and self.auth_token and self.from_number)
        
        if self.enabled:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            logger.warning("Twilio credentials not found. WhatsApp notifications are disabled.")

    def send_message(self, to_number: str, message: str) -> bool:
        if not self.enabled:
            logger.warning(f"Simulating WhatsApp message to {to_number}: {message}")
            return False
            
        try:
            # Ensure number is formatted for WhatsApp
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
                
            from_formatted = self.from_number
            if not from_formatted.startswith("whatsapp:"):
                from_formatted = f"whatsapp:{from_formatted}"
                
            msg = self.client.messages.create(
                body=message,
                from_=from_formatted,
                to=to_number
            )
            logger.info(f"WhatsApp message sent to {to_number}. SID: {msg.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to_number}: {e}")
            return False

    def broadcast_alert(self, db: Session, message: str) -> int:
        """
        Sends a WhatsApp message to all users who have opted in.
        Returns the number of messages successfully sent.
        """
        users = (
            db.query(User)
            .join(UserSettings, User.id == UserSettings.user_id)
            .filter(
                User.phone_number.isnot(None),
                User.phone_number != "",
                UserSettings.whatsapp_notifications == True
            )
            .all()
        )
        
        count = 0
        for user in users:
            if user.phone_number:
                success = self.send_message(user.phone_number, message)
                if success:
                    count += 1
                    
        return count

# Global instance
notifier = WhatsAppNotifier()
