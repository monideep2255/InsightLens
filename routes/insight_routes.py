from flask import Blueprint, render_template, jsonify, request, current_app, abort, redirect, url_for
from models import Document, Insight, Processing, db
import datetime

bp = Blueprint('insight_routes', __name__)

@bp.route('/insights/<int:document_id>')
def show_insights(document_id):
    """
    Display insights for a specific document
    """
    document = Document.query.get_or_404(document_id)
    insights = Insight.query.filter_by(document_id=document_id).all()
    
    return render_template('insights.html', document=document, insights=insights)

@bp.route('/api/processing/<int:document_id>')
def check_processing_status(document_id):
    """
    API endpoint to check the processing status of a document
    """
    processing = Processing.query.filter_by(document_id=document_id).first()
    
    if not processing:
        return jsonify({
            'status': 'unknown',
            'message': 'No processing record found for this document'
        })
    
    result = {
        'status': processing.status,
        'started_at': processing.started_at.isoformat() if processing.started_at else None,
        'completed_at': processing.completed_at.isoformat() if processing.completed_at else None
    }
    
    if processing.error:
        result['error'] = processing.error
    
    return jsonify(result)
    
@bp.route('/api/processing/<int:document_id>/cancel', methods=['POST'])
def cancel_processing(document_id):
    """
    Cancel processing for a document
    """
    document = Document.query.get_or_404(document_id)
    processing = Processing.query.filter_by(document_id=document_id).first()
    
    if not processing:
        return jsonify({
            'status': 'error',
            'message': 'No processing record found for this document'
        }), 404
    
    # Only allow cancellation if the document is still being processed
    if processing.status not in ['pending', 'processing']:
        return jsonify({
            'status': 'error',
            'message': f'Cannot cancel processing in status: {processing.status}'
        }), 400
    
    # Update the processing record to mark it as cancelled
    processing.status = 'cancelled'
    processing.error = 'Processing cancelled by user'
    processing.completed_at = datetime.datetime.utcnow()
    
    # Update the document to mark it as processed (to prevent further processing attempts)
    document.processed = True
    
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Processing cancelled successfully'
    })

@bp.route('/document/<int:document_id>/cancel', methods=['GET', 'POST'])
def cancel_processing_redirect(document_id):
    """
    Cancel processing and redirect to home page
    """
    processing = Processing.query.filter_by(document_id=document_id).first()
    document = Document.query.get_or_404(document_id)
    
    if processing and processing.status in ['pending', 'processing']:
        # Update the processing record
        processing.status = 'cancelled'
        processing.error = 'Processing cancelled by user'
        processing.completed_at = datetime.datetime.utcnow()
        
        # Update the document
        document.processed = True
        
        db.session.commit()
    
    return redirect(url_for('document_routes.index'))
