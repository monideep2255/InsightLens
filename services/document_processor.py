import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

from app import db, app
from models import Document, Insight, Processing, ApiUsage
from services.pdf_parser import extract_pdf_content
from services.ai_service import generate_insights
# Import the demo service
from services.demo_service import generate_demo_insights, perform_local_analysis
# Import the edgar service if it exists
try:
    from services.edgar_service import extract_10k_content
    EDGAR_SERVICE_AVAILABLE = True
except ImportError:
    EDGAR_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)

def process_document(document_id):
    """Process a document and generate insights"""
    # Get document from database
    document = Document.query.get(document_id)
    if not document:
        logger.error(f"Document with ID {document_id} not found")
        return False
    
    # Create or update processing entry
    processing = Processing.query.filter_by(document_id=document.id).first()
    if not processing:
        processing = Processing(document_id=document.id)
        db.session.add(processing)
    
    processing.status = 'processing'
    db.session.commit()
    
    try:
        # Check if we should use demo mode
        if document.use_demo_mode:
            # Use appropriate demo template based on content type or company name
            company_type = "tech"  # Default
            
            # Try to guess company type from title or filename
            doc_text = (document.title or "") + " " + (document.filename or "") + " " + (document.company_name or "")
            doc_text = doc_text.lower()
            
            if any(term in doc_text for term in ["bank", "financial", "insurance", "invest", "capital"]):
                company_type = "financial"
            elif any(term in doc_text for term in ["retail", "store", "shop", "consumer"]):
                company_type = "retail"
            elif any(term in doc_text for term in ["manufacturing", "industrial", "factory"]):
                company_type = "manufacturing"
            
            logger.info(f"Using demo mode with {company_type} template for document {document_id}")
            
            # Get demo insights
            insights = generate_demo_insights(document_id, company_type)
            
            # Add a note that this is demo mode
            for category in insights:
                insights[category] = f"<div class='alert alert-info'>DEMO MODE: This is sample data for demonstration purposes.</div>{insights[category]}"
                
        else:
            # Regular processing mode - extract content based on document type
            if document.content_type == 'pdf':
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, document.filename)
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"PDF file not found: {file_path}")
                
                content = extract_pdf_content(file_path)
            elif document.content_type == 'edgar' and EDGAR_SERVICE_AVAILABLE:
                # If we have a CIK, use that to get the 10-K directly
                if document.cik:
                    from services.edgar_service import get_latest_10k
                    filing_url = get_latest_10k(document.cik)
                    if not filing_url:
                        raise ValueError(f"Could not find 10-K filing for CIK: {document.cik}")
                    content = extract_10k_content(filing_url)
                else:
                    # Otherwise use the URL we were given
                    content = extract_10k_content(document.url)
            else:
                raise ValueError(f"Unsupported content type: {document.content_type}")
            
            if not content:
                raise ValueError("Could not extract any content from the document. The document may be empty or in an unsupported format.")
                
            if len(content.strip()) < 500:
                logger.warning(f"Document {document_id} has very little content: {len(content.strip())} characters")
                
                # For 10-K filings, provide a more specific error message
                if document.content_type == 'edgar':
                    raise ValueError("Could not extract sufficient content from the SEC filing. This could be due to the filing using a newer format that our system cannot process. Please try a different company or upload a PDF version of the 10-K if available.")
            
            # Generate insights using either AI or local processing
            if document.use_local_processing:
                logger.info(f"Using local processing for document {document_id}")
                insights = perform_local_analysis(content)
                
                # Add a note that this is local processing mode
                for category in insights:
                    insights[category] = f"<div class='alert alert-info'>LOCAL PROCESSING: This analysis was performed locally without AI.</div>{insights[category]}"
            else:
                # Generate insights using AI and track usage
                insights = generate_insights(content)
                
                # Monitor token usage - this would normally be provided by the API response
                # Since we don't have direct access to token counts, we'll estimate based on content length
                try:
                    # Rough estimate: 1 token ≈ 4 characters
                    estimated_prompt_tokens = len(content) // 4
                    estimated_completion_tokens = sum(len(insight) for insight in insights.values()) // 4
                    
                    # Calculate estimated cost
                    estimated_cost = ApiUsage.calculate_openai_cost(
                        estimated_prompt_tokens, 
                        estimated_completion_tokens
                    )
                    
                    # Record API usage
                    api_usage = ApiUsage(
                        api_name="openai",  # Default to OpenAI, could be changed based on config
                        document_id=document.id,
                        prompt_tokens=estimated_prompt_tokens,
                        completion_tokens=estimated_completion_tokens,
                        estimated_cost_usd=estimated_cost
                    )
                    db.session.add(api_usage)
                    logger.info(f"Recorded API usage: {estimated_prompt_tokens} prompt tokens, {estimated_completion_tokens} completion tokens, ${estimated_cost:.4f} est. cost")
                except Exception as usage_error:
                    logger.error(f"Error recording API usage: {str(usage_error)}")
        
        # Save insights to database
        for category, insight_content in insights.items():
            # Check if insight for this category already exists
            existing_insight = Insight.query.filter_by(
                document_id=document.id,
                category=category
            ).first()
            
            if existing_insight:
                existing_insight.content = insight_content
            else:
                new_insight = Insight(
                    document_id=document.id,
                    category=category,
                    content=insight_content
                )
                db.session.add(new_insight)
        
        # Update document and processing status
        document.processed = True
        processing.status = 'completed'
        processing.completed_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Successfully processed document {document_id}")
        return True
    
    except Exception as e:
        # Handle any errors during processing
        logger.exception(f"Error processing document {document_id}: {str(e)}")
        processing.status = 'failed'
        processing.error = str(e)
        processing.completed_at = datetime.utcnow()
        db.session.commit()
        return False

def save_uploaded_file(file):
    """Save an uploaded file to the uploads directory"""
    filename = secure_filename(file.filename)
    # Add timestamp to filename to prevent collisions
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{timestamp}_{filename}"
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    return unique_filename
