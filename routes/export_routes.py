"""
Routes for exporting document insights to various formats (PDF, etc.)
"""
from flask import Blueprint, send_from_directory, render_template, redirect, url_for, request, flash, jsonify, abort, current_app
import os

from app import db
from models import Document, Insight
from services.pdf_export import create_pdf_export
from services.document_processor import get_document_content
from services.ai_service import generate_insights

# Create the blueprint
export_bp = Blueprint('export', __name__)

@export_bp.route('/document/<int:document_id>/export/pdf')
def export_to_pdf(document_id):
    """
    Export document insights to PDF
    """
    # Check if document exists
    document = Document.query.get_or_404(document_id)
    
    # Get document insights
    insights = Insight.query.filter_by(document_id=document.id).all()
    
    # Generate PDF export
    pdf_path = create_pdf_export(document, insights)
    
    # Determine the directory name (exports)
    dir_name = os.path.dirname(pdf_path)
    file_name = os.path.basename(pdf_path)
    
    # Serve the file
    return send_from_directory(dir_name, file_name, as_attachment=True)


@export_bp.route('/api/document/<int:document_id>/export/pdf', methods=['POST'])
def api_export_to_pdf(document_id):
    """
    API endpoint to export document insights to PDF
    """
    # Check if document exists
    document = Document.query.get_or_404(document_id)
    
    # Get document insights
    insights = Insight.query.filter_by(document_id=document.id).all()
    
    # Generate PDF export
    try:
        pdf_path = create_pdf_export(document, insights)
        
        # Return success with file URL
        return jsonify({
            'success': True,
            'pdf_url': url_for('export.export_to_pdf', document_id=document.id)
        })
    except Exception as e:
        # Return error
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@export_bp.route('/document/<int:document_id>/regenerate/<category>', methods=['POST'])
def regenerate_insight(document_id, category):
    """
    Regenerate a specific insight category
    """
    # Check if document exists
    document = Document.query.get_or_404(document_id)
    
    # Get document content
    content = get_document_content(document)
    
    if not content:
        flash('Could not retrieve document content.', 'error')
        return redirect(url_for('insight.show_insights', document_id=document_id))
    
    try:
        # Generate new insights for the specific category
        new_insights = generate_insights(
            content, 
            filter_categories=[category]
        )
        
        if category in new_insights:
            # Remove old insights for this category
            old_insights = Insight.query.filter_by(document_id=document.id, category=category).all()
            for insight in old_insights:
                db.session.delete(insight)
            
            # Create new insight for the category
            new_insight = Insight(
                document_id=document.id,
                category=category,
                content=new_insights[category]
            )
            db.session.add(new_insight)
            db.session.commit()
            
            flash(f'Successfully regenerated {category} insights.', 'success')
        else:
            flash(f'Failed to regenerate {category} insights.', 'error')
    
    except Exception as e:
        flash(f'Error regenerating insights: {str(e)}', 'error')
    
    return redirect(url_for('insight.show_insights', document_id=document_id))