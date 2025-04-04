import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "insightlens_secret_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Initialize SQLAlchemy with app
db.init_app(app)

# Import routes
from routes import document_routes, insight_routes, edgar_routes, admin_routes, comparison_routes

# Register blueprints
app.register_blueprint(document_routes.bp)
app.register_blueprint(insight_routes.bp)
app.register_blueprint(edgar_routes.bp)
app.register_blueprint(admin_routes.admin_bp)
app.register_blueprint(comparison_routes.comparison_bp)

with app.app_context():
    # Import models
    import models
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create all database tables
    db.create_all()
