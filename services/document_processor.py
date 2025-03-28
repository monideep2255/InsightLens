import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

from app import db
from models import Document, Insight, Processing
from services.pdf_parser import extract_pdf_content
from services.url_parser import extract_url_content
from services.ai_service import generate_insights

logger = logging.getLogger(__name__)

def process_document(document_id):
    """Process a document and generate insights"""
    # Get document from database
    document = Document.query.get(document_id)
    if not document:
        logger.error(f"Document with ID {document_id} not found")
        return False
    
    # Create or update processing entry
    processing = Processing.query.filter_by(document_id=document.id).first()
    if not processing:
        processing = Processing(document_id=document.id)
        db.session.add(processing)
    
    processing.status = 'processing'
    db.session.commit()
    
    try:
        # Extract content based on document type
        if document.content_type == 'pdf':
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, document.filename)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            
            content = extract_pdf_content(file_path)
        elif document.content_type == 'url':
            content = extract_url_content(document.url)
        else:
            raise ValueError(f"Unsupported content type: {document.content_type}")
        
        if not content or len(content.strip()) < 100:
            raise ValueError("Could not extract sufficient content from the document")
        
        # Generate insights using AI
        insights = generate_insights(content)
        
        # Save insights to database
        for category, insight_content in insights.items():
            # Check if insight for this category already exists
            existing_insight = Insight.query.filter_by(
                document_id=document.id,
                category=category
            ).first()
            
            if existing_insight:
                existing_insight.content = insight_content
            else:
                new_insight = Insight(
                    document_id=document.id,
                    category=category,
                    content=insight_content
                )
                db.session.add(new_insight)
        
        # Update document and processing status
        document.processed = True
        processing.status = 'completed'
        processing.completed_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Successfully processed document {document_id}")
        return True
    
    except Exception as e:
        # Handle any errors during processing
        logger.exception(f"Error processing document {document_id}: {str(e)}")
        processing.status = 'failed'
        processing.error = str(e)
        processing.completed_at = datetime.utcnow()
        db.session.commit()
        return False

def save_uploaded_file(file):
    """Save an uploaded file to the uploads directory"""
    filename = secure_filename(file.filename)
    # Add timestamp to filename to prevent collisions
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{filename}"
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    return unique_filename
