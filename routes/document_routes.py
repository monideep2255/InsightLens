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
    """Handle document upload (PDF only)"""
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
            
        elif upload_type == 'quick_edgar':
            # Handle quick access to SEC EDGAR for the Magnificent 7 companies
            cik = request.form.get('cik')
            if not cik:
                flash('Please select a company', 'danger')
                return redirect(request.url)
            
            # Get company name
            company_name = request.form.get('company_name', '').strip()
            
            # Map of company names for the Magnificent 7
            magnificent_7 = {
                '0000320193': 'Apple Inc.',
                '0000789019': 'Microsoft Corporation',
                '0001018724': 'Amazon.com, Inc.',
                '0001652044': 'Alphabet Inc. (Google)',
                '0001326801': 'Meta Platforms, Inc. (Facebook)',
                '0001318605': 'Tesla, Inc.',
                '0000885639': 'NVIDIA Corporation'
            }
            
            # Use the name from our map if available
            if not company_name and cik in magnificent_7:
                company_name = magnificent_7[cik]
            
            # For demo mode, we'll skip the actual SEC fetch
            if use_demo_mode:
                document = Document(
                    url=f"https://www.sec.gov/dummy/edgar/data/{cik}",
                    content_type='edgar',
                    use_demo_mode=True,
                    use_local_processing=use_local_processing,
                    company_name=company_name,
                    title=f"{company_name} - SEC EDGAR (Demo)" if company_name else f"SEC EDGAR Document ({cik}) - Demo",
                    cik=cik
                )
                db.session.add(document)
                db.session.commit()
            else:
                # Pass along demo_mode and local_processing URL parameters if they're set
                demo_mode_param = request.args.get('demo_mode')
                demo_param = request.args.get('demo')
                local_processing_param = request.args.get('local_processing')
                
                url_params = {'cik': cik, 'company_name': company_name}
                
                # Add params only if they exist
                if demo_mode_param:
                    url_params['demo_mode'] = demo_mode_param
                if demo_param:
                    url_params['demo'] = demo_param
                if local_processing_param:
                    url_params['local_processing'] = local_processing_param
                    
                # For real processing, redirect to the edgar route which has better handling
                return redirect(url_for('edgar.process_10k', **url_params))
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
