from flask import Blueprint, render_template, jsonify, request, current_app, abort
from models import Document, Insight, Processing

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
