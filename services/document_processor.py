import os
import logging
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

from app import db, app
from models import Document, Insight, Processing, ApiUsage
from services.pdf_parser import extract_pdf_content
from services.ai_service import generate_insights, PROMPT_TEMPLATES
# Import the demo service
from services.demo_service import generate_demo_insights, perform_local_analysis
# Import the edgar service if it exists
try:
    from services.edgar_service import extract_10k_content
    EDGAR_SERVICE_AVAILABLE = True
except ImportError:
    EDGAR_SERVICE_AVAILABLE = False

# Try to import the cache service
try:
    from services.cache_service import clear_old_cache_entries, get_cache_stats
    CACHE_SERVICE_AVAILABLE = True
except ImportError:
    CACHE_SERVICE_AVAILABLE = False

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
        # Start processing timer
        start_time = time.time()
        
        # Check if we should use demo mode
        if document.use_demo_mode:
            # Use appropriate demo template based on content type, company name, or industry type
            company_type = "tech"  # Default
            
            # First check if we have an industry type specified explicitly
            if document.industry_type:
                if document.industry_type.lower() in ["financial", "banking", "insurance", "investment"]:
                    company_type = "financial"
                elif document.industry_type.lower() in ["retail", "consumer", "ecommerce"]:
                    company_type = "retail"
                elif document.industry_type.lower() in ["manufacturing", "industrial"]:
                    company_type = "manufacturing"
                elif document.industry_type.lower() in ["biotech", "pharmaceutical", "healthcare"]:
                    company_type = "biotech"
                elif document.industry_type.lower() in ["technology", "software", "it"]:
                    company_type = "tech"
            else:
                # Try to guess company type from title or filename
                doc_text = (document.title or "") + " " + (document.filename or "") + " " + (document.company_name or "")
                doc_text = doc_text.lower()
                
                if any(term in doc_text for term in ["bank", "financial", "insurance", "invest", "capital"]):
                    company_type = "financial"
                elif any(term in doc_text for term in ["retail", "store", "shop", "consumer"]):
                    company_type = "retail"
                elif any(term in doc_text for term in ["manufacturing", "industrial", "factory"]):
                    company_type = "manufacturing"
                elif any(term in doc_text for term in ["biotech", "pharma", "drug", "medical", "health"]):
                    company_type = "biotech"
            
            logger.info(f"Using demo mode with {company_type} template for document {document_id}")
            
            # Get demo insights
            demo_start_time = time.time()
            insights = generate_demo_insights(document_id, company_type)
            demo_time = time.time() - demo_start_time
            logger.info(f"Demo insights generated in {demo_time:.2f} seconds")
            
            # Add a note that this is demo mode
            for category in insights:
                insights[category] = f"<div class='alert alert-info'>DEMO MODE: This is sample data for demonstration purposes.</div>{insights[category]}"
                
        else:
            # Regular processing mode - extract content based on document type
            extraction_start_time = time.time()
            
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
            
            extraction_time = time.time() - extraction_start_time
            logger.info(f"Content extraction completed in {extraction_time:.2f} seconds")
            
            if not content:
                raise ValueError("Could not extract any content from the document. The document may be empty or in an unsupported format.")
                
            if len(content.strip()) < 500:
                logger.warning(f"Document {document_id} has very little content: {len(content.strip())} characters")
                
                # For 10-K filings, provide a more specific error message
                if document.content_type == 'edgar':
                    raise ValueError("Could not extract sufficient content from the SEC filing. This could be due to the filing using a newer format that our system cannot process. Please try a different company or upload a PDF version of the 10-K if available.")
            
            logger.info(f"Extracted content length: {len(content)} characters")
            
            # Generate insights using either AI or local processing
            if document.use_local_processing:
                logger.info(f"Using local processing for document {document_id}")
                local_start_time = time.time()
                insights = perform_local_analysis(content)
                local_time = time.time() - local_start_time
                logger.info(f"Local processing completed in {local_time:.2f} seconds")
                
                # Add a note that this is local processing mode
                for category in insights:
                    insights[category] = f"<div class='alert alert-info'>LOCAL PROCESSING: This analysis was performed locally without AI.</div>{insights[category]}"
            else:
                # Generate insights using AI and track usage
                ai_start_time = time.time()
                
                # Start with basic categories
                categories_to_include = ['business_summary', 'moat', 'financial', 'management']
                categories_to_exclude = []
                
                # Determine additional prompt templates to use based on document options
                additional_prompts = {}
                
                # Add enhanced moat analysis for all documents (Phase 2.1 feature)
                additional_prompts['moat_analysis'] = True
                logger.info(f"Using enhanced moat analysis for document {document_id}")
                
                # Add margin of safety commentary for all documents (Phase 2.1 feature) 
                additional_prompts['margin_of_safety'] = True
                logger.info(f"Adding margin of safety commentary for document {document_id}")
                
                # Add red flags detection for all documents
                additional_prompts['red_flags'] = True
                logger.info(f"Adding red flags detection for document {document_id}")
                
                # Add Buffett analysis if requested (Phase 2.2 feature)
                if document.use_buffett_mode:
                    additional_prompts['buffett_analysis'] = True
                    logger.info(f"Using Warren Buffett analysis mode for document {document_id}")
                
                # Add biotech analysis if requested or if the industry is detected as biotech (Phase 2.2 feature)
                if document.use_biotech_mode or (document.industry_type and 
                    document.industry_type.lower() in ["biotech", "pharmaceutical", "healthcare"]):
                    additional_prompts['biotech_analysis'] = True
                    logger.info(f"Using biotech company analysis mode for document {document_id}")
                
                # Add or remove categories based on industry type
                if document.industry_type:
                    industry = document.industry_type.lower()
                    
                    # For financial companies, prioritize financial analysis
                    if industry in ["financial", "banking", "insurance", "investment"]:
                        # Add the financial_institutions analysis if available
                        if 'financial_institutions' in PROMPT_TEMPLATES:
                            additional_prompts['financial_institutions'] = True
                            logger.info(f"Adding financial institutions analysis for {industry} company")
                    
                    # For retail companies, focus on consumer insights
                    elif industry in ["retail", "consumer", "ecommerce"]:
                        # Add the retail_analysis if available
                        if 'retail_analysis' in PROMPT_TEMPLATES:
                            additional_prompts['retail_analysis'] = True
                            logger.info(f"Adding retail analysis for {industry} company")
                            
                    # For technology companies, focus on tech moats and innovation
                    elif industry in ["technology", "software", "it"]:
                        # Add the tech_analysis if available
                        if 'tech_analysis' in PROMPT_TEMPLATES:
                            additional_prompts['tech_analysis'] = True
                            logger.info(f"Adding technology analysis for {industry} company")
                
                # Generate insights with the specialized templates, using the filter categories mechanism
                insights = generate_insights(
                    content, 
                    additional_prompt_templates=additional_prompts,
                    filter_categories=categories_to_include,
                    exclude_categories=categories_to_exclude
                )
                
                ai_time = time.time() - ai_start_time
                logger.info(f"AI insights generated in {ai_time:.2f} seconds")
                
                # Note: Now that we're using filtered categories in the generate_insights function,
                # we don't need the separate code for specialized analysis anymore, since it's all handled
                # by the additional_prompt_templates parameter and the filter_categories mechanism.
                # The code below is kept for backward compatibility and will be deprecated in future versions.
                
                # Check if we need to manually add analysis for any categories that might have been missed
                # This can happen if the model doesn't support all the requested categories
                
                # Check if Buffett analysis is missing but requested
                if document.use_buffett_mode and 'buffett_analysis' not in insights:
                    logger.info(f"Adding missing Buffett-style analysis for document {document_id}")
                    from services.ai_service import PROMPT_TEMPLATES
                    buffett_prompt = PROMPT_TEMPLATES['buffett_analysis'].format(content=content)
                    
                    if os.environ.get("HUGGINGFACE_API_KEY"):
                        from services.open_source_ai import analyze_with_prompt
                        buffett_insight = analyze_with_prompt(content, buffett_prompt)
                    else:
                        from services.ai_service import get_openai_client
                        client = get_openai_client()
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "You are Warren Buffett analyzing a potential investment."},
                                {"role": "user", "content": buffett_prompt}
                            ],
                            temperature=0.3
                        )
                        buffett_insight = response.choices[0].message.content
                    
                    insights['buffett_analysis'] = buffett_insight
                
                # Check if red flags analysis is missing but requested
                if 'red_flags' not in insights:
                    logger.info(f"Adding missing red flags analysis for document {document_id}")
                    from services.ai_service import PROMPT_TEMPLATES
                    red_flags_prompt = PROMPT_TEMPLATES['red_flags'].format(content=content)
                    
                    if os.environ.get("HUGGINGFACE_API_KEY"):
                        from services.open_source_ai import analyze_with_prompt
                        red_flags_insight = analyze_with_prompt(content, red_flags_prompt)
                    else:
                        from services.ai_service import get_openai_client
                        client = get_openai_client()
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "You are a forensic financial analyst specializing in detecting red flags."},
                                {"role": "user", "content": red_flags_prompt}
                            ],
                            temperature=0.3
                        )
                        red_flags_insight = response.choices[0].message.content
                    
                    insights['red_flags'] = red_flags_insight
                
                # Check if moat analysis is missing (Phase 2.1 feature)
                if 'moat_analysis' not in insights:
                    logger.info(f"Adding missing enhanced moat analysis for document {document_id}")
                    from services.new_prompt_templates import NEW_PROMPT_TEMPLATES
                    moat_prompt = NEW_PROMPT_TEMPLATES['moat_analysis'].format(content=content)
                    
                    # First try with Hugging Face if available
                    if os.environ.get("HUGGINGFACE_API_KEY"):
                        try:
                            from services.open_source_ai import analyze_with_prompt
                            moat_insight = analyze_with_prompt(content, moat_prompt)
                            if "<p>Error calling AI service" in moat_insight or "402 Client Error" in moat_insight:
                                # Hugging Face failed, fall back to OpenAI if available
                                raise Exception("Hugging Face API failed, falling back to OpenAI")
                        except Exception as e:
                            logger.warning(f"Hugging Face API error: {str(e)}, falling back to OpenAI")
                            # Fall back to OpenAI
                            if os.environ.get("OPENAI_API_KEY"):
                                from services.ai_service import get_openai_client
                                client = get_openai_client()
                                response = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "You are Warren Buffett analyzing a company's competitive advantages."},
                                        {"role": "user", "content": moat_prompt}
                                    ],
                                    temperature=0.3
                                )
                                moat_insight = response.choices[0].message.content
                            else:
                                moat_insight = "<p>Unable to generate analysis. Both Hugging Face and OpenAI services are unavailable.</p>"
                    else:
                        # Use OpenAI directly if no Hugging Face API key
                        from services.ai_service import get_openai_client
                        client = get_openai_client()
                        if client:
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "You are Warren Buffett analyzing a company's competitive advantages."},
                                    {"role": "user", "content": moat_prompt}
                                ],
                                temperature=0.3
                            )
                            moat_insight = response.choices[0].message.content
                        else:
                            moat_insight = "<p>Unable to generate analysis. No AI service is available.</p>"
                    
                    insights['moat_analysis'] = moat_insight
                
                # Check if margin of safety analysis is missing (Phase 2.1 feature)
                if 'margin_of_safety' not in insights:
                    logger.info(f"Adding missing margin of safety analysis for document {document_id}")
                    from services.new_prompt_templates import NEW_PROMPT_TEMPLATES
                    margin_prompt = NEW_PROMPT_TEMPLATES['margin_of_safety'].format(content=content)
                    
                    # First try with Hugging Face if available
                    if os.environ.get("HUGGINGFACE_API_KEY"):
                        try:
                            from services.open_source_ai import analyze_with_prompt
                            margin_insight = analyze_with_prompt(content, margin_prompt)
                            if "<p>Error calling AI service" in margin_insight or "402 Client Error" in margin_insight:
                                # Hugging Face failed, fall back to OpenAI if available
                                raise Exception("Hugging Face API failed, falling back to OpenAI")
                        except Exception as e:
                            logger.warning(f"Hugging Face API error: {str(e)}, falling back to OpenAI")
                            # Fall back to OpenAI
                            if os.environ.get("OPENAI_API_KEY"):
                                from services.ai_service import get_openai_client
                                client = get_openai_client()
                                response = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "You are a value investor evaluating the margin of safety for a potential investment."},
                                        {"role": "user", "content": margin_prompt}
                                    ],
                                    temperature=0.3
                                )
                                margin_insight = response.choices[0].message.content
                            else:
                                margin_insight = "<p>Unable to generate analysis. Both Hugging Face and OpenAI services are unavailable.</p>"
                    else:
                        # Use OpenAI directly if no Hugging Face API key
                        from services.ai_service import get_openai_client
                        client = get_openai_client()
                        if client:
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "You are a value investor evaluating the margin of safety for a potential investment."},
                                    {"role": "user", "content": margin_prompt}
                                ],
                                temperature=0.3
                            )
                            margin_insight = response.choices[0].message.content
                        else:
                            margin_insight = "<p>Unable to generate analysis. No AI service is available.</p>"
                    
                    insights['margin_of_safety'] = margin_insight
                
                # Check if biotech analysis is missing but requested
                if document.use_biotech_mode and 'biotech_analysis' not in insights:
                    logger.info(f"Adding missing biotech-specific analysis for document {document_id}")
                    from services.new_prompt_templates import NEW_PROMPT_TEMPLATES
                    biotech_prompt = NEW_PROMPT_TEMPLATES['biotech_analysis'].format(content=content)
                    
                    if os.environ.get("HUGGINGFACE_API_KEY"):
                        from services.open_source_ai import analyze_with_prompt
                        biotech_insight = analyze_with_prompt(content, biotech_prompt)
                    else:
                        from services.ai_service import get_openai_client
                        client = get_openai_client()
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "You are a specialized analyst evaluating a biotech/pharmaceutical company."},
                                {"role": "user", "content": biotech_prompt}
                            ],
                            temperature=0.3
                        )
                        biotech_insight = response.choices[0].message.content
                    
                    insights['biotech_analysis'] = biotech_insight
                
                # Monitor token usage - this would normally be provided by the API response
                # Since we don't have direct access to token counts, we'll estimate based on content length
                try:
                    # Determine which API was used based on environment variables
                    api_name = "huggingface" if os.environ.get("HUGGINGFACE_API_KEY") else "openai"
                    
                    # Rough estimate: 1 token ≈ 4 characters
                    estimated_prompt_tokens = len(content) // 4
                    estimated_completion_tokens = sum(len(insight) for insight in insights.values()) // 4
                    
                    # Calculate estimated cost based on API used
                    if api_name == "openai":
                        estimated_cost = ApiUsage.calculate_openai_cost(
                            estimated_prompt_tokens, 
                            estimated_completion_tokens
                        )
                    else:
                        # Hugging Face pricing is variable, use a conservative estimate
                        estimated_cost = (estimated_prompt_tokens * 0.00001) + (estimated_completion_tokens * 0.00002)
                    
                    # Record API usage
                    api_usage = ApiUsage(
                        api_name=api_name,
                        document_id=document.id,
                        prompt_tokens=estimated_prompt_tokens,
                        completion_tokens=estimated_completion_tokens,
                        estimated_cost_usd=estimated_cost
                    )
                    db.session.add(api_usage)
                    logger.info(f"Recorded API usage: {estimated_prompt_tokens} prompt tokens, {estimated_completion_tokens} completion tokens, ${estimated_cost:.4f} est. cost")
                except Exception as usage_error:
                    logger.error(f"Error recording API usage: {str(usage_error)}")
            
            # Clean up cache if available
            if CACHE_SERVICE_AVAILABLE:
                try:
                    cache_start_time = time.time()
                    cleared_entries = clear_old_cache_entries(max_age_days=7)
                    cache_time = time.time() - cache_start_time
                    if cleared_entries > 0:
                        logger.info(f"Cleared {cleared_entries} old cache entries in {cache_time:.2f} seconds")
                    
                    # Get cache stats
                    cache_stats = get_cache_stats()
                    logger.info(f"Cache statistics: {cache_stats}")
                except Exception as cache_error:
                    logger.warning(f"Error managing cache: {str(cache_error)}")
        
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
        
        # Calculate and log total processing time
        total_time = time.time() - start_time
        logger.info(f"Successfully processed document {document_id} in {total_time:.2f} seconds")
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


def get_document_content(document):
    """
    Retrieve document content based on its type
    
    Args:
        document (Document): Document object from the database
        
    Returns:
        str: Document content, or None if content could not be retrieved
    """
    try:
        if document.content_type == 'pdf':
            upload_folder = current_app.config['UPLOAD_FOLDER']
            file_path = os.path.join(upload_folder, document.filename)
            if not os.path.exists(file_path):
                logger.error(f"PDF file not found: {file_path}")
                return None
            
            return extract_pdf_content(file_path)
            
        elif document.content_type == 'edgar' and EDGAR_SERVICE_AVAILABLE:
            # If we have a CIK, use that to get the 10-K directly
            if document.cik:
                from services.edgar_service import get_latest_10k
                filing_url = get_latest_10k(document.cik)
                if not filing_url:
                    logger.error(f"Could not find 10-K filing for CIK: {document.cik}")
                    return None
                return extract_10k_content(filing_url)
            else:
                # Otherwise use the URL we were given
                return extract_10k_content(document.url)
                
        else:
            logger.error(f"Unsupported content type: {document.content_type}")
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving document content: {str(e)}")
        return None
