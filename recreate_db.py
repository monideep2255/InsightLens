import os
from app import app, db
import models  # Import the models to ensure they are registered

# Main application
if __name__ == "__main__":
    with app.app_context():
        print("Dropping all existing tables...")
        db.drop_all()
        
        print("Creating all tables from models...")
        db.create_all()
        
        print("Database schema has been successfully recreated!")