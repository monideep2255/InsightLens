from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
import logging
import threading
from models import Document, Processing
from app import db
from services.edgar_service import search_company, get_latest_10k, extract_10k_content
from services.document_processor import process_document

bp = Blueprint('edgar', __name__, url_prefix='/edgar')
logger = logging.getLogger(__name__)


@bp.route('/search', methods=['GET', 'POST'])
def search():
    """
    Search for companies in SEC EDGAR database
    """
    # Handle the query parameter for GET requests from the main page
    if request.method == 'GET' and request.args.get('query'):
        company_name = request.args.get('query', '')
        if not company_name:
            return render_template('edgar_search.html', error='Please enter a company name')
        
        companies = search_company(company_name)
        return render_template('edgar_search.html', companies=companies, query=company_name)
    # Handle POST requests from the edgar_search page form
    elif request.method == 'POST':
        company_name = request.form.get('company_name', '')
        if not company_name:
            return render_template('edgar_search.html', error='Please enter a company name')
        
        companies = search_company(company_name)
        return render_template('edgar_search.html', companies=companies, query=company_name)
    
    return render_template('edgar_search.html')


@bp.route('/process/<cik>', methods=['GET'])
def process_10k(cik):
    """
    Process the latest 10-K filing for a company
    """
    try:
        # Get company name if provided
        company_name = request.args.get('company_name', '')
        
        # Get the latest 10-K URL
        filing_url = get_latest_10k(cik)
        if not filing_url:
            return render_template('edgar_search.html', error='Could not find 10-K filing for this company. The SEC may have changed their filing format.')
        
        # Map of CIK to company names for the Magnificent 7
        magnificent_7 = {
            '0000320193': 'Apple Inc.',
            '0000789019': 'Microsoft Corporation',
            '0001018724': 'Amazon.com, Inc.',
            '0001652044': 'Alphabet Inc. (Google)',
            '0001326801': 'Meta Platforms, Inc. (Facebook)',
            '0001318605': 'Tesla, Inc.',
            '0000885639': 'NVIDIA Corporation'
        }
        
        # If no company name provided but it's one of the Magnificent 7, use that name
        if not company_name and cik in magnificent_7:
            company_name = magnificent_7[cik]
            
        # Always enable demo mode by default to avoid API issues
        # User can still disable it explicitly by passing demo_mode=false in the URL
        use_demo_mode = request.args.get('demo_mode', 'true').lower() != 'false'
        use_local_processing = request.args.get('local_processing', 'false').lower() == 'true'
        
        # Create a new document with better metadata
        document = Document(
            url=filing_url,
            content_type='edgar',  # Use 'edgar' type instead of 'url' for better handling
            title=f"10-K Filing: {company_name or 'Unknown Company'}",
            company_name=company_name,
            cik=cik,
            use_demo_mode=use_demo_mode,
            use_local_processing=use_local_processing
        )
        db.session.add(document)
        db.session.commit()
        
        # Create processing entry
        processing = Processing(document_id=document.id)
        db.session.add(processing)
        db.session.commit()
        
        # Start processing in a background thread with app context
        from app import app
        
        def process_with_app_context(doc_id):
            with app.app_context():
                success = process_document(doc_id)
                
                # If processing fails, log additional details
                if not success:
                    proc = Processing.query.filter_by(document_id=doc_id).first()
                    logger.error(f"Processing failed for document {doc_id}, error: {proc.error if proc else 'Unknown error'}")
                
        thread = threading.Thread(target=process_with_app_context, args=(document.id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started processing 10-K for {company_name or cik} (Document ID: {document.id})")
        return redirect(url_for('insight_routes.show_insights', document_id=document.id))
        
    except Exception as e:
        logger.error(f"Error processing 10-K for CIK {cik}: {str(e)}")
        error_message = str(e)
        
        # Provide more user-friendly error messages
        if "Could not find 10-K filing" in error_message:
            error_message = "Could not find a recent 10-K filing for this company. Please try another company or use the SEC search feature."
        elif "Connection" in error_message or "Timeout" in error_message:
            error_message = "Connection to the SEC database timed out. This could be due to high traffic. Please try again later."
        
        return render_template('edgar_search.html', error=f"Error processing 10-K: {error_message}")