"""
PDF Export service for InsightLens

This module provides functionality to export document insights to PDF format
"""
import os
import logging
import time
import datetime
from flask import current_app
import re

# Import ReportLab components for PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

logger = logging.getLogger(__name__)

# Define constants
EXPORT_FOLDER = 'static/exports'
LOGO_PATH = 'static/img/logo.png'  # Path to the logo image

# Create custom styles for the PDF
def get_custom_styles():
    """Get custom styles for the PDF document"""
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=1,  # Center alignment
        spaceAfter=20
    )
    
    # Subtitle style
    subtitle_style = ParagraphStyle(
        name='SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=10
    )
    
    # Document info style
    info_style = ParagraphStyle(
        name='InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray
    )
    
    # Category header style
    category_style = ParagraphStyle(
        name='CategoryStyle',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.blue
    )
    
    # Normal text style
    normal_style = ParagraphStyle(
        name='NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'info': info_style,
        'category': category_style,
        'normal': normal_style
    }

def create_pdf_export(document, insights):
    """
    Create a PDF export of document insights
    
    Args:
        document: The document object
        insights: List of insight objects
        
    Returns:
        str: Path to the generated PDF file (relative to static directory)
    """
    # Ensure the export directory exists
    if not os.path.exists(EXPORT_FOLDER):
        os.makedirs(EXPORT_FOLDER)
    
    # Generate a unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"insights_{document.id}_{timestamp}.pdf"
    filepath = os.path.join(EXPORT_FOLDER, filename)
    
    # Get custom styles
    styles = get_custom_styles()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        title=f"InsightLens Analysis - {document.title or 'Document'}",
        author="InsightLens",
        subject="Financial Document Analysis"
    )
    
    # Elements to add to the PDF
    elements = []
    
    # Add title
    elements.append(Paragraph("InsightLens Analysis", styles['title']))
    
    # Add document title
    elements.append(Paragraph(document.title or "Document Analysis", styles['subtitle']))
    
    # Add document info
    info_text = f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if document.company_name:
        info_text += f"<br/>Company: {document.company_name}"
    if document.content_type == 'edgar' and document.cik:
        info_text += f"<br/>CIK: {document.cik}"
    elements.append(Paragraph(info_text, styles['info']))
    
    # Add some space
    elements.append(Spacer(1, 20))
    
    # Convert insights list to dictionary for easier processing
    insights_dict = {}
    for insight in insights:
        insights_dict[insight.category] = insight.content
    
    # Define the order of categories to display
    category_order = [
        'business_summary',
        'moat',
        'moat_analysis',
        'financial',
        'margin_of_safety',
        'management',
        'red_flags',
        'buffett_analysis',
        'biotech_analysis',
        'financial_institutions',
        'retail_analysis',
        'tech_analysis'
    ]
    
    # Map categories to user-friendly names
    category_names = {
        'business_summary': 'Business Summary',
        'moat': 'Competitive Advantage',
        'moat_analysis': 'Enhanced Moat Analysis',
        'financial': 'Financial Health',
        'margin_of_safety': 'Margin of Safety',
        'management': 'Management Quality',
        'red_flags': 'Red Flags and Risk Factors',
        'buffett_analysis': 'Warren Buffett Analysis',
        'biotech_analysis': 'Biotech Company Analysis',
        'financial_institutions': 'Financial Institution Analysis',
        'retail_analysis': 'Retail Sector Analysis',
        'tech_analysis': 'Technology Company Analysis'
    }
    
    # Process insights in the specified order
    for category in category_order:
        if category in insights_dict:
            # Add category header
            elements.append(Paragraph(category_names.get(category, category.title()), styles['category']))
            
            # Process the content (remove HTML tags)
            content = insights_dict[category]
            content = re.sub(r'<div class=["\']alert alert-\w+["\']>.*?</div>', '', content)  # Remove alert divs
            content = re.sub(r'<[^>]+>', '', content)  # Remove HTML tags
            
            # Add the content
            elements.append(Paragraph(content, styles['normal']))
            
            # Add a spacer
            elements.append(Spacer(1, 10))
    
    # Build the PDF
    doc.build(elements)
    
    logger.info(f"Generated PDF export at {filepath}")
    
    # Return the path relative to the static directory
    relative_path = os.path.join('exports', filename)
    return relative_path