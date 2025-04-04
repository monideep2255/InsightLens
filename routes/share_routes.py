"""
Routes for managing shareable links for document insights
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort, current_app
from datetime import datetime, timedelta

from app import db
from models import Document, Insight, ShareableLink

# Create the blueprint
share_bp = Blueprint('share', __name__)

@share_bp.route('/document/<int:document_id>/share', methods=['GET', 'POST'])
def create_shareable_link(document_id):
    """
    Create a shareable link for a document
    """
    # Check if document exists
    document = Document.query.get_or_404(document_id)
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '')
        expires_days = request.form.get('expires_days')
        
        # Convert expires_days to integer if provided
        if expires_days and expires_days.strip():
            try:
                expires_days = int(expires_days)
            except ValueError:
                expires_days = None
        else:
            expires_days = None
            
        # Create shareable link
        link = ShareableLink.create_for_document(document_id, name, expires_days)
        
        flash('Shareable link created successfully!', 'success')
        return redirect(url_for('share.manage_links', document_id=document_id))
    
    # GET request - show the form
    return render_template('share/create_link.html', document=document)


@share_bp.route('/shared/<token>')
def view_shared_document(token):
    """
    View a document shared via a shareable link
    """
    # Look up the token
    link = ShareableLink.query.filter_by(token=token).first_or_404()
    
    # Check if link is valid (active and not expired)
    if not link.is_valid():
        # Link has expired or been deactivated
        return render_template('share/link_expired.html')
    
    # Get the document and insights
    document = link.document
    insights = Insight.query.filter_by(document_id=document.id).all()
    
    # Convert insights to a dictionary for easier template access
    insights_dict = {}
    for insight in insights:
        insights_dict[insight.category] = insight.content
    
    # Render the shared insights view
    return render_template('share/shared_insights.html', 
                          document=document, 
                          insights=insights_dict,
                          shareable_link=link)


@share_bp.route('/document/<int:document_id>/manage-links')
def manage_links(document_id):
    """
    Manage shareable links for a document
    """
    # Check if document exists
    document = Document.query.get_or_404(document_id)
    
    # Get all shareable links for this document
    links = ShareableLink.query.filter_by(document_id=document_id).all()
    
    return render_template('share/manage_links.html', document=document, links=links)


@share_bp.route('/document/<int:document_id>/deactivate-link/<int:link_id>', methods=['POST'])
def deactivate_link(document_id, link_id):
    """
    Deactivate a shareable link
    """
    # Check if document exists
    document = Document.query.get_or_404(document_id)
    
    # Check if link exists and belongs to this document
    link = ShareableLink.query.filter_by(id=link_id, document_id=document_id).first_or_404()
    
    # Deactivate the link
    link.is_active = False
    db.session.commit()
    
    flash('Shareable link deactivated successfully!', 'success')
    return redirect(url_for('share.manage_links', document_id=document_id))


@share_bp.route('/api/document/<int:document_id>/share', methods=['POST'])
def api_create_link(document_id):
    """
    API endpoint to create a shareable link
    """
    # Check if document exists
    document = Document.query.get_or_404(document_id)
    
    # Get JSON data
    data = request.get_json() or {}
    name = data.get('name', '')
    expires_days = data.get('expires_days')
    
    # Create shareable link
    try:
        link = ShareableLink.create_for_document(document_id, name, expires_days)
        
        # Return the link details
        return jsonify({
            'success': True,
            'link': {
                'id': link.id,
                'token': link.token,
                'url': url_for('share.view_shared_document', token=link.token, _external=True),
                'name': link.name,
                'created_at': link.created_at.isoformat(),
                'expires_at': link.expires_at.isoformat() if link.expires_at else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500