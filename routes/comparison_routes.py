"""
Routes for document comparison functionality
"""

from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash, session
from models import Document, db
import logging
from services.document_comparison import compare_documents

# Setup logging
logger = logging.getLogger(__name__)

# Create blueprint
comparison_bp = Blueprint('comparison', __name__)

@comparison_bp.route('/comparison', methods=['GET'])
def comparison_page():
    """
    Display the document comparison page
    """
    # Get all processed documents for selection
    documents = Document.query.filter_by(processed=True).order_by(Document.created_at.desc()).all()
    
    return render_template('comparison.html', documents=documents)

@comparison_bp.route('/compare', methods=['POST'])
def compare():
    """
    Process document comparison request
    """
    try:
        # Get selected document IDs from form
        doc_ids = request.form.getlist('document_ids')
        
        # Convert to integers
        doc_ids = [int(doc_id) for doc_id in doc_ids if doc_id]
        
        if len(doc_ids) < 2:
            flash('Please select at least 2 documents to compare', 'warning')
            return redirect(url_for('comparison.comparison_page'))
        
        # Store in session for results page
        session['comparison_doc_ids'] = doc_ids
        
        # Redirect to results page, which will handle the actual comparison
        return redirect(url_for('comparison.comparison_results'))
    
    except Exception as e:
        logger.error(f"Error in comparison request: {str(e)}")
        flash(f"Error processing comparison: {str(e)}", 'danger')
        return redirect(url_for('comparison.comparison_page'))

@comparison_bp.route('/comparison-results', methods=['GET'])
def comparison_results():
    """
    Display document comparison results
    """
    # Get document IDs from session
    doc_ids = session.get('comparison_doc_ids')
    
    if not doc_ids or len(doc_ids) < 2:
        flash('No documents selected for comparison', 'warning')
        return redirect(url_for('comparison.comparison_page'))
    
    # Get document information for display
    documents = Document.query.filter(Document.id.in_(doc_ids)).all()
    
    # Perform the comparison
    comparison_results = compare_documents(doc_ids)
    
    # Check for errors
    if 'error' in comparison_results:
        flash(comparison_results['error'], 'danger')
        return redirect(url_for('comparison.comparison_page'))
    
    return render_template(
        'comparison_results.html', 
        results=comparison_results,
        documents=documents
    )

@comparison_bp.route('/api/compare', methods=['POST'])
def api_compare():
    """
    API endpoint for document comparison
    """
    try:
        data = request.get_json()
        if not data or 'document_ids' not in data:
            return jsonify({'error': 'Missing document_ids parameter'}), 400
        
        doc_ids = data['document_ids']
        
        if len(doc_ids) < 2:
            return jsonify({'error': 'Please select at least 2 documents to compare'}), 400
        
        # Perform the comparison
        comparison_results = compare_documents(doc_ids)
        
        return jsonify(comparison_results)
    
    except Exception as e:
        logger.error(f"API error in comparison request: {str(e)}")
        return jsonify({'error': str(e)}), 500