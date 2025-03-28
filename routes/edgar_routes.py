from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import logging
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
        # Get the latest 10-K URL
        filing_url = get_latest_10k(cik)
        if not filing_url:
            return render_template('edgar_search.html', error='Could not find 10-K filing for this company')
        
        # Create a new document
        document = Document(
            url=filing_url,
            content_type='url',
            title=f"10-K Filing (CIK: {cik})"
        )
        db.session.add(document)
        db.session.commit()
        
        # Create processing entry
        processing = Processing(document_id=document.id)
        db.session.add(processing)
        db.session.commit()
        
        # Start processing in background
        # In a production environment, this would be done with a task queue
        # but for simplicity, we'll process it here (may cause timeout issues for large documents)
        process_document(document.id)
        
        return redirect(url_for('insight_routes.show_insights', document_id=document.id))
        
    except Exception as e:
        logger.error(f"Error processing 10-K for CIK {cik}: {str(e)}")
        return render_template('edgar_search.html', error=f"Error processing 10-K: {str(e)}")