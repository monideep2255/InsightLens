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
    
    # Processing options
    use_demo_mode = request.form.get('use_demo_mode') == 'on'
    use_local_processing = request.form.get('use_local_processing') == 'on'
    company_name = request.form.get('company_name', '').strip()
    
    try:
        if upload_type == 'file':
            # Handle PDF file upload
            if 'file' not in request.files and not use_demo_mode:
                flash('No file part', 'danger')
                return redirect(request.url)
            
            if use_demo_mode:
                # Create new document in database with demo mode
                document = Document(
                    filename="demo_file.pdf",
                    content_type='pdf',
                    use_demo_mode=True,
                    use_local_processing=use_local_processing,
                    company_name=company_name,
                    title=f"Demo: {company_name}" if company_name else "Demo Document"
                )
            else:
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
                    content_type='pdf',
                    use_demo_mode=use_demo_mode,
                    use_local_processing=use_local_processing,
                    company_name=company_name,
                    title=f"{company_name}" if company_name else filename
                )
            
            db.session.add(document)
            db.session.commit()
            
        elif upload_type == 'url':
            # Handle URL input
            url = request.form.get('url')
            if not url or len(url.strip()) == 0 and not use_demo_mode:
                flash('Please enter a valid URL', 'danger')
                return redirect(request.url)
            
            if use_demo_mode:
                # Create demo document with URL type
                document = Document(
                    url="https://example.com/demo",
                    content_type='url',
                    use_demo_mode=True,
                    use_local_processing=use_local_processing,
                    company_name=company_name,
                    title=f"Demo: {company_name}" if company_name else "Demo URL Document"
                )
            else:
                # Create new document in database
                document = Document(
                    url=url,
                    content_type='url',
                    use_demo_mode=use_demo_mode,
                    use_local_processing=use_local_processing,
                    company_name=company_name,
                    title=f"{company_name}" if company_name else url
                )
            
            db.session.add(document)
            db.session.commit()
            
        elif upload_type == 'quick_edgar':
            # Handle quick access to SEC EDGAR for popular companies
            cik = request.form.get('cik')
            if not cik:
                flash('Please select a company', 'danger')
                return redirect(request.url)
            
            # Get company name
            company_name = request.form.get('company_name', '').strip()
            
            # Create direct EDGAR URL
            base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}"
            
            # Create new document in database
            document = Document(
                url=base_url,
                content_type='edgar',
                use_demo_mode=use_demo_mode,
                use_local_processing=use_local_processing,
                company_name=company_name,
                title=f"{company_name} - SEC EDGAR" if company_name else f"SEC EDGAR Document ({cik})",
                cik=cik
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
        from app import app
        
        def process_with_app_context(doc_id):
            with app.app_context():
                process_document(doc_id)
                
        thread = threading.Thread(target=process_with_app_context, args=(document.id,))
        thread.daemon = True
        thread.start()
        
        # Add friendly message for demo mode
        if use_demo_mode:
            flash('Using demo mode - no external APIs will be called.', 'info')
        elif use_local_processing:
            flash('Using local processing - analysis will be performed without AI.', 'info')
        
        # Redirect to insights page
        return redirect(url_for('insight_routes.show_insights', document_id=document.id))
        
    except Exception as e:
        current_app.logger.error(f"Error during upload: {str(e)}")
        flash(f"Error during upload: {str(e)}", 'danger')
        return redirect(url_for('document_routes.index'))
