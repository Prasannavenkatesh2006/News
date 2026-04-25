ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) NULL;
ALTER TABLE user_settings ADD COLUMN whatsapp_notifications BOOLEAN DEFAULT FALSE;
