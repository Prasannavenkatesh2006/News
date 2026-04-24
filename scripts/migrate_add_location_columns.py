"""
Run this script to add country/state/city columns and indexes to the articles table.
Intended to be executed inside the `api` or from host with psql available.
"""
import os
import sys
from sqlalchemy import create_engine, text

DB_URL = os.getenv('DATABASE_URL') or os.getenv('DATABASE') or os.getenv('POSTGRES_URL')
if not DB_URL:
    # Fallback to environment variables used by the project
    user = os.getenv('POSTGRES_USER', 'postgres')
    pwd = os.getenv('POSTGRES_PASSWORD', '')
    host = os.getenv('POSTGRES_HOST', 'postgres')
    port = os.getenv('POSTGRES_PORT', '5432')
    db = os.getenv('POSTGRES_DB', 'anip')
    DB_URL = f'postgresql://{user}:{pwd}@{host}:{port}/{db}'

engine = create_engine(DB_URL)

sql = """
ALTER TABLE newsarticle
  ADD COLUMN IF NOT EXISTS country VARCHAR(100),
  ADD COLUMN IF NOT EXISTS state VARCHAR(100),
  ADD COLUMN IF NOT EXISTS city VARCHAR(100);

CREATE INDEX IF NOT EXISTS idx_newsarticle_country ON newsarticle(country);
CREATE INDEX IF NOT EXISTS idx_newsarticle_state ON newsarticle(state);

-- Tamil Nadu view
CREATE OR REPLACE VIEW tamil_nadu_news AS
SELECT * FROM newsarticle
WHERE state = 'Tamil Nadu'
   OR (country = 'India' AND (
        title ILIKE '%chennai%' OR
        title ILIKE '%tamil nadu%' OR
        content ILIKE '%tamil nadu%'
   ))
ORDER BY published_at DESC;
"""

def main():
    with engine.begin() as conn:
        conn.execute(text(sql))
    print('✅ Migration applied: location columns, indexes, and view created/updated')


if __name__ == '__main__':
    main()
