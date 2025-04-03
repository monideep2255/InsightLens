import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# DATABASE_URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable is not set.")
    sys.exit(1)

try:
    # Connect to the database
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    # Begin transaction
    trans = conn.begin()
    
    # Check if insight table exists (to know if we're creating or updating)
    check_sql = text("SELECT to_regclass('public.insight');")
    insight_exists = conn.execute(check_sql).scalar() is not None
    
    if insight_exists:
        print("Database tables already exist - updating schema...")
        
        # Add new columns to document table
        try:
            print("Adding new columns to document table...")
            conn.execute(text("ALTER TABLE document ADD COLUMN IF NOT EXISTS use_buffett_mode BOOLEAN DEFAULT false"))
            conn.execute(text("ALTER TABLE document ADD COLUMN IF NOT EXISTS use_biotech_mode BOOLEAN DEFAULT false"))
            conn.execute(text("ALTER TABLE document ADD COLUMN IF NOT EXISTS industry_type VARCHAR(64)"))
            
            # Add severity column to insight table
            print("Adding severity column to insight table...")
            conn.execute(text("ALTER TABLE insight ADD COLUMN IF NOT EXISTS severity VARCHAR(20)"))
            
        except SQLAlchemyError as e:
            print(f"Error during schema update: {e}")
            trans.rollback()
            sys.exit(1)
            
    else:
        print("Creating database tables from scratch...")
        
        # Import models and create tables
        try:
            from app import app
            from models import db
            with app.app_context():
                db.create_all()
        except Exception as e:
            print(f"Error creating tables: {e}")
            trans.rollback()
            sys.exit(1)
    
    # Commit changes
    trans.commit()
    print("Database schema update complete!")
    
except SQLAlchemyError as e:
    print(f"Database error: {e}")
    sys.exit(1)
finally:
    conn.close()
    engine.dispose()