import os
import threading
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from werkzeug.utils import secure_filename

from app import db
from models import Document, Processing
from services.document_processor import save_uploaded_file, process_document

bp = Blueprint('document_routes', __name__)

@bp.route('/')
def index():
    """Render the main upload page"""
    return render_template('index.html')

@bp.route('/upload', methods=['POST'])
def upload_document():
    """Handle document upload (PDF or URL)"""
    upload_type = request.form.get('upload_type', 'file')
    
    try:
        if upload_type == 'file':
            # Handle PDF file upload
            if 'file' not in request.files:
                flash('No file part', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'danger')
                return redirect(request.url)
            
            if not file.filename.lower().endswith('.pdf'):
                flash('Only PDF files are supported', 'danger')
                return redirect(request.url)
            
            # Save the uploaded file
            filename = save_uploaded_file(file)
            
            # Create new document in database
            document = Document(
                filename=filename,
                content_type='pdf'
            )
            db.session.add(document)
            db.session.commit()
            
        elif upload_type == 'url':
            # Handle URL input
            url = request.form.get('url')
            if not url or len(url.strip()) == 0:
                flash('Please enter a valid URL', 'danger')
                return redirect(request.url)
            
            # Create new document in database
            document = Document(
                url=url,
                content_type='url'
            )
            db.session.add(document)
            db.session.commit()
            
        else:
            flash('Invalid upload type', 'danger')
            return redirect(request.url)
        
        # Create processing record
        processing = Processing(document_id=document.id)
        db.session.add(processing)
        db.session.commit()
        
        # Start processing in a background thread with app context
        def process_with_app_context(doc_id):
            with current_app.app_context():
                process_document(doc_id)
                
        thread = threading.Thread(target=process_with_app_context, args=(document.id,))
        thread.daemon = True
        thread.start()
        
        # Redirect to insights page
        return redirect(url_for('insight_routes.show_insights', document_id=document.id))
        
    except Exception as e:
        current_app.logger.error(f"Error during upload: {str(e)}")
        flash(f"Error during upload: {str(e)}", 'danger')
        return redirect(url_for('document_routes.index'))
