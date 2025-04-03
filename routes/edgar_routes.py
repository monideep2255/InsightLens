from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
import logging
import threading
import requests
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
        # Get company name from the query parameters (from the search results page)
        # The company name may come from either a query parameter or the form
        company_name = request.args.get('company_name', '') or request.args.get('name', '')
        
        # If it's coming from search results, extract the company name from the SIC info
        if company_name and 'SIC:' in company_name:
            company_name = company_name.split('SIC:')[0].strip()
        
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
            
        # Check if we should use demo mode (from URL parameter)
        use_demo_mode = request.args.get('demo_mode') == 'true' or request.args.get('demo') == 'true'
        use_local_processing = request.args.get('local_processing') == 'true'
        use_buffett_mode = request.args.get('use_buffett_mode') == 'true' or request.args.get('buffett_mode') == 'true'
        use_biotech_mode = request.args.get('use_biotech_mode') == 'true' or request.args.get('biotech_mode') == 'true'
        industry_type = request.args.get('industry_type', '')
        
        # If company_name is not provided, try to get it from the SEC API
        if not company_name:
            # Try to get company name from the magnificent_7 map
            if cik in magnificent_7:
                company_name = magnificent_7[cik]
            else:
                # Try to extract company name from filing URL or response
                try:
                    response = requests.get(filing_url, headers={'User-Agent': 'InsightLens Research Tool (contactus@example.com)'})
                    if response.status_code == 200:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')
                        # Try to find company name in title
                        title_tag = soup.find('title')
                        if title_tag and not 'EDGAR' in title_tag.text:
                            # Extract company name from title
                            title_text = title_tag.text.strip()
                            if ':' in title_text:
                                # Format: "Company Name: 10-K Filing"
                                company_name = title_text.split(':')[0].strip()
                            elif '-' in title_text:
                                # Format: "10-K - Company Name"
                                company_name = title_text.split('-')[1].strip()
                            else:
                                # Just use the title
                                company_name = title_text
                except Exception as e:
                    logger.warning(f"Failed to extract company name from filing URL: {str(e)}")
            
            # If we still don't have a company name, try getting it from the SEC API
            if not company_name:
                try:
                    # Format CIK with leading zeros for API request
                    cik_padded = cik.zfill(10)
                    headers = {'User-Agent': 'InsightLens Research Tool (contactus@example.com)'}
                    api_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
                    response = requests.get(api_url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        if 'name' in data:
                            company_name = data['name']
                except Exception as e:
                    logger.warning(f"Failed to get company name from SEC API: {str(e)}")
        
        # If we still don't have a company name, use a placeholder with the CIK
        if not company_name:
            company_name = f"Company CIK: {cik}"
        
        # Clean the company name - remove any CIK references
        if 'CIK#:' in company_name:
            company_name = company_name.split('CIK#:')[0].strip()
            
        # Create a new document with better metadata
        document = Document(
            url=filing_url,
            content_type='edgar',  # Use 'edgar' type instead of 'url' for better handling
            title=f"10-K Filing: {company_name}",
            company_name=company_name,
            cik=cik,
            use_demo_mode=use_demo_mode,
            use_local_processing=use_local_processing,
            use_buffett_mode=use_buffett_mode,
            use_biotech_mode=use_biotech_mode,
            industry_type=industry_type
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