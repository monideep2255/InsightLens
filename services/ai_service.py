import os
import json
import logging
import requests
from services.new_prompt_templates import NEW_PROMPT_TEMPLATES

# Optional import of OpenAI
OPENAI_AVAILABLE = False
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

# AI Model Configuration - read from environment
AI_MODEL_TYPE = os.environ.get("AI_MODEL_TYPE", "huggingface").lower()  # Default to Hugging Face
HUGGINGFACE_MODEL = os.environ.get("HUGGINGFACE_MODEL", "mistral")  # Default Hugging Face model

# Initialize OpenAI client functions
def get_openai_client(validate=True):
    """
    Get an OpenAI client with the latest API key from environment variables
    
    Args:
        validate (bool): Whether to validate the API key with a test request
        
    Returns:
        OpenAI client or None if unavailable/invalid
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        return None
    
    # Log API key format for debugging (securely)
    key_prefix = api_key[:8] if len(api_key) > 8 else "too_short"
    logger.debug(f"Initializing OpenAI client with API key starting with {key_prefix}...")
    
    # Create and return the client
    try:
        client = OpenAI(api_key=api_key)
        
        # Optionally validate the client with a simple request
        if validate:
            try:
                # Make a lightweight request to validate the API key
                models = client.models.list(limit=1)
                logger.info("OpenAI API key validated successfully")
            except Exception as validation_error:
                logger.error(f"OpenAI API key validation failed: {str(validation_error)}")
                
                # Check for specific error types
                error_msg = str(validation_error).lower()
                if "authentication" in error_msg or "invalid" in error_msg or "unauthorized" in error_msg:
                    logger.critical("OpenAI API key appears to be invalid - please check your API key")
                    return None
                elif "rate limit" in error_msg or "ratelimit" in error_msg:
                    logger.warning("OpenAI API rate limit exceeded. Will proceed with client but requests may fail.")
                elif "timeout" in error_msg or "connection" in error_msg:
                    logger.warning("OpenAI API connection issue. Will proceed with client but requests may be slow.")
        
        logger.debug("OpenAI client created successfully")
        return client
    except Exception as e:
        logger.error(f"Error creating OpenAI client: {str(e)}")
        return None

# Initialize a global variable for reference, but we'll refresh before each use
if AI_MODEL_TYPE == "openai" and OPENAI_AVAILABLE:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not found in environment variables")

# Initialize Hugging Face setup if selected
if AI_MODEL_TYPE == "huggingface":
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
    if not HUGGINGFACE_API_KEY:
        logger.warning("HUGGINGFACE_API_KEY not found in environment variables")
    
    # Model options for Hugging Face
    HUGGINGFACE_MODEL_OPTIONS = {
        "deepseek": "deepseek-ai/deepseek-coder-33b-instruct",
        "llama3": "meta-llama/Llama-3-8b-chat-hf",
        "mistral": "mistralai/Mixtral-8x7B-Instruct-v0.1"
    }

# Import the new prompt templates from new_prompt_templates.py
try:
    from services.new_prompt_templates import NEW_PROMPT_TEMPLATES
    logger.info(f"Imported {len(NEW_PROMPT_TEMPLATES)} new prompt templates")
except ImportError as e:
    logger.error(f"Error importing new prompt templates: {str(e)}")
    NEW_PROMPT_TEMPLATES = {}

# Prompt templates - Base templates
BASE_PROMPT_TEMPLATES = {
    'business_summary': """
You are an expert business analyst reviewing a company document.

Based on the provided content, explain this company's business model in plain language.
- What do they sell or build?
- Who are their customers?
- What industry are they in?
- What problem do they solve?

Format your response as a concise, well-structured HTML that clearly explains what the company does.
Focus on objective facts from the document, not speculation.

DOCUMENT CONTENT:
{content}
""",

    'moat': """
You are a value investor assessing competitive advantages.

Based on the provided content, analyze whether the company has a durable competitive advantage (moat).
Consider these types of moats:
- Brand (consumer recognition and loyalty)
- Network Effects (service value increases with more users)
- Intellectual Property (patents, trademarks, trade secrets)
- Cost Advantage (economies of scale, proprietary technology)
- Switching Costs (difficult/expensive for customers to switch)
- Regulatory advantages

Format your response as HTML with these sections:
1. Type of Moat (or None Detected)
2. Justification (2-3 sentences)
3. Supporting Evidence (quote from document, if available)

Be honest if no clear moat is detected from the available information.

DOCUMENT CONTENT:
{content}
""",

    'financial': """
You are a financial analyst reviewing company documents.

Extract 3-5 key financial signals or ratios from the document. Focus specifically on:
- Revenue trend
- Debt levels
- Profitability or free cash flow
- Return on equity or assets (if mentioned)
- Gross margins or operating margins

Format your response as HTML with a concise bullet-point list of the financial metrics you found.
Include specific numbers when available, and note trends (increasing/decreasing).
If certain key financial information seems to be missing, note this as well.

DOCUMENT CONTENT:
{content}
""",

    'management': """
You are a governance expert evaluating company management.

Based on tone, quotes, and information in the document, what can you infer about the management team?
Consider:
- Leadership experience and track record
- Transparency in communication
- Alignment with shareholders
- Focus on long-term vs. short-term results
- Compensation structure (if mentioned)

Format your response as HTML with a concise assessment of management quality based only on what's in the document.
If there's insufficient information to make a judgment, clearly state that.

DOCUMENT CONTENT:
{content}
"""
}

# Combine base templates with new ones
PROMPT_TEMPLATES = {**BASE_PROMPT_TEMPLATES, **NEW_PROMPT_TEMPLATES}

def generate_insights(content, additional_prompt_templates=None, filter_categories=None, exclude_categories=None):
    """
    Generate structured insights from document content using the configured AI model
    Returns a dictionary mapping insight categories to their content
    
    Args:
        content (str): The document content to analyze
        additional_prompt_templates (dict, optional): A dictionary mapping additional prompt template 
            names to boolean values indicating whether to include them in the analysis
        filter_categories (list, optional): A list of category names to include (if specified, only these 
            categories will be analyzed)
        exclude_categories (list, optional): A list of category names to exclude from analysis
    """
    # Default categories to analyze
    if filter_categories:
        # If filter_categories is provided, start with only those categories
        categories_to_analyze = [category for category in filter_categories if category in PROMPT_TEMPLATES]
        logger.info(f"Using filtered categories: {categories_to_analyze}")
    else:
        # Otherwise use the standard set
        categories_to_analyze = ['business_summary', 'moat', 'financial', 'management']
    
    # Add additional prompt templates if specified
    if additional_prompt_templates:
        for template_name, include in additional_prompt_templates.items():
            if include and template_name in PROMPT_TEMPLATES and template_name not in categories_to_analyze:
                categories_to_analyze.append(template_name)
                logger.info(f"Adding additional template: {template_name}")
    
    # Apply exclusions if specified
    if exclude_categories:
        categories_to_analyze = [category for category in categories_to_analyze if category not in exclude_categories]
        logger.info(f"After exclusions, analyzing categories: {categories_to_analyze}")
    
    # Check for cached results first
    try:
        # Import here to avoid circular imports
        from services.cache_service import get_cached_ai_response, save_ai_response
        
        # Get combined prompt for cache key
        combined_prompt = "".join(PROMPT_TEMPLATES[category] for category in categories_to_analyze if category in PROMPT_TEMPLATES)
        
        # Look for cached responses
        cached_insights = get_cached_ai_response(content, combined_prompt, AI_MODEL_TYPE)
        if cached_insights:
            logger.info("Using cached insights")
            # Filter the cached insights to only include the requested categories
            filtered_cached_insights = {category: content for category, content in cached_insights.items() 
                                      if category in categories_to_analyze}
            return filtered_cached_insights
    except ImportError:
        logger.warning("Cache service not available, skipping cache check")
    except Exception as cache_error:
        logger.warning(f"Error checking cache: {str(cache_error)}")
        
    # No cached results, generate new insights
    try:
        if AI_MODEL_TYPE == "openai" and OPENAI_AVAILABLE:
            insights = generate_insights_with_openai(content, categories_to_analyze)
        elif AI_MODEL_TYPE == "huggingface":
            insights = generate_insights_with_huggingface(content, categories_to_analyze)
        else:
            logger.error(f"Invalid AI model type: {AI_MODEL_TYPE}")
            return {
                category: f"<p>AI model configuration error. Please check server logs.</p>" 
                for category in categories_to_analyze
            }
        
        # Cache the results
        try:
            from services.cache_service import save_ai_response
            # Get combined prompt for cache key - include all requested categories
            combined_prompt = "".join(PROMPT_TEMPLATES[category] for category in categories_to_analyze if category in PROMPT_TEMPLATES)
            save_ai_response(content, combined_prompt, AI_MODEL_TYPE, insights)
        except Exception as cache_save_error:
            logger.warning(f"Error saving to cache: {str(cache_save_error)}")
            
        return insights
        
    except Exception as e:
        logger.error(f"All AI models failed to generate insights: {str(e)}")
        error_message = str(e)
        
        # Check for quota exceeded messages
        if "quota" in error_message.lower() or "429" in error_message:
            return {
                category: "<p>API quota exceeded. Please check your account billing or try again later.</p>"
                for category in categories_to_analyze
            }
        
        # Generic error fallback
        return {
            category: f"<p>Unable to generate insights. Error: {error_message}</p>"
            for category in categories_to_analyze
        }

def optimize_content_for_analysis(content, token_budget=8000):
    """
    Optimize document content for analysis by fitting it within a token budget
    
    Args:
        content (str): The original document content
        token_budget (int): Maximum number of tokens to use for the content
    
    Returns:
        str: Optimized content that fits within the token budget
    """
    from models import ApiUsage  # Import here to avoid circular imports
    
    # Utility function to estimate token count
    def estimate_token_count(text):
        # Rough approximation: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    # Check usage limits to see if we need to be aggressive with optimization
    usage_status = ApiUsage.check_usage_limits()
    
    # Adjust token budget based on current usage
    if usage_status["usage_percent"] > 90:
        # We're close to the budget limit, be very conservative
        token_budget = token_budget // 2
        logger.warning(f"API usage at {usage_status['usage_percent']:.1f}% of budget, reducing token budget to {token_budget}")
    elif usage_status["usage_percent"] > 75:
        # We're approaching the budget limit
        token_budget = int(token_budget * 0.75)
        logger.info(f"API usage at {usage_status['usage_percent']:.1f}% of budget, reducing token budget to {token_budget}")
    
    # Estimate token count for the full content
    estimated_tokens = estimate_token_count(content)
    
    # If content fits within budget, return it as is
    if estimated_tokens <= token_budget:
        logger.info(f"Content fits within token budget ({estimated_tokens}/{token_budget})")
        return content
    
    # If content is too large, we need to optimize it
    logger.info(f"Content exceeds token budget ({estimated_tokens}/{token_budget}), optimizing")
    
    # Strategy 1: If very large content, extract a summary
    # For large documents, this is more efficient than sending the full text
    if estimated_tokens > token_budget * 2:
        # Create a summary of key points from a portion of the document
        sample_size = min(len(content), token_budget * 4)  # Sample to stay within token limits
        return create_content_summary(content[:sample_size], token_budget)
    
    # Strategy 2: Extract important sections
    # Take beginning, middle, and end portions
    beginning_size = token_budget // 3
    middle_size = token_budget // 3
    end_size = token_budget - beginning_size - middle_size
    
    # Extract sections
    beginning = content[:beginning_size * 4]  # Convert tokens to approx chars
    
    # Only include middle if document is long enough
    if len(content) > (beginning_size + end_size) * 4 * 2:
        mid_point = len(content) // 2
        middle_start = mid_point - (middle_size * 2)
        middle_end = mid_point + (middle_size * 2)
        middle = content[max(0, middle_start):min(len(content), middle_end)]
    else:
        middle = ""
    
    # End section
    end = content[-end_size * 4:] if len(content) > end_size * 4 else ""
    
    # Combine the sections
    optimized_content = f"""
    BEGINNING OF DOCUMENT:
    {beginning}
    
    {'MIDDLE OF DOCUMENT:' if middle else ''}
    {middle}
    
    {'END OF DOCUMENT:' if end else ''}
    {end}
    """
    
    # Final check to ensure we're within budget
    if estimate_token_count(optimized_content) > token_budget:
        # If still too large, truncate further
        return optimized_content[:token_budget * 4]
    
    return optimized_content

def create_content_summary(content, token_budget=3000):
    """
    Create a summary of the content to fit within token budget
    
    Args:
        content (str): The content to summarize
        token_budget (int): Maximum number of tokens for the result
    
    Returns:
        str: A summarized version of the content
    """
    # Check if we have OpenAI API access for summarization
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # No OpenAI access, do manual extraction of key sections
        logger.warning("No OpenAI API key for summarization, using manual extraction")
        return extract_key_sections(content, token_budget)
    
    logger.info("Using OpenAI to create content summary")
    
    # Create a summarization prompt
    summary_prompt = f"""
    Summarize the key business points in this document in 1000 words or less.
    Focus on extracting facts about:
    1. The company's business model and products/services
    2. Market position and competitive advantages
    3. Financial metrics mentioned
    4. Management statements and strategy
    
    DOCUMENT CONTENT:
    {content}
    """
    
    try:
        # Generate a summary using OpenAI
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        client = get_openai_client()
        if not client:
            raise Exception("OpenAI API key not configured or invalid")
            
        summary_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a business analyst who extracts key facts from documents."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Extract summary
        summary = summary_response.choices[0].message.content
        
        # Track API usage
        from models import ApiUsage, db
        api_usage = ApiUsage(
            api_name="openai",
            document_id=None,  # This is a preprocessing step, not tied to a document
            prompt_tokens=len(summary_prompt) // 4,
            completion_tokens=len(summary) // 4,
            estimated_cost_usd=ApiUsage.calculate_openai_cost(len(summary_prompt) // 4, len(summary) // 4),
            model_name="gpt-4o",
            request_successful=True
        )
        db.session.add(api_usage)
        db.session.commit()
        
        return f"DOCUMENT SUMMARY:\n{summary}"
    
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        # Fall back to manual extraction
        return extract_key_sections(content, token_budget)

def extract_key_sections(content, token_budget=3000):
    """
    Extract key sections from content based on heuristics
    
    Args:
        content (str): The content to extract from
        token_budget (int): Maximum number of tokens for the result
        
    Returns:
        str: Extracted key sections
    """
    # Approximate character budget (4 chars per token)
    char_budget = token_budget * 4
    
    # Extract common sections of interest
    sections = []
    
    # Look for business description section
    business_keywords = ["Business Overview", "Company Overview", "Description of Business", "Our Business"]
    for keyword in business_keywords:
        if keyword in content:
            # Extract paragraph after keyword
            start_idx = content.find(keyword)
            end_idx = content.find("\n\n", start_idx + len(keyword))
            if end_idx == -1:
                end_idx = min(start_idx + 1500, len(content))
            sections.append(content[start_idx:end_idx])
    
    # Look for financial section
    financial_keywords = ["Financial Overview", "Financial Results", "Financial Highlights"]
    for keyword in financial_keywords:
        if keyword in content:
            start_idx = content.find(keyword)
            end_idx = content.find("\n\n", start_idx + len(keyword))
            if end_idx == -1:
                end_idx = min(start_idx + 1500, len(content))
            sections.append(content[start_idx:end_idx])
    
    # Combine sections
    extracted_content = "\n\n".join(sections)
    
    # If we haven't found key sections or they're too small, add beginning and end
    if len(extracted_content) < char_budget // 2:
        beginning = content[:char_budget // 3]
        end = content[-char_budget // 3:] if len(content) > char_budget // 3 else ""
        
        extracted_content = f"{extracted_content}\n\nBEGINNING OF DOCUMENT:\n{beginning}\n\nEND OF DOCUMENT:\n{end}"
    
    # Final size check
    if len(extracted_content) > char_budget:
        return extracted_content[:char_budget]
    
    return extracted_content

def generate_insights_with_openai(content, categories_to_analyze=None):
    """
    Generate insights using OpenAI's API
    
    Args:
        content (str): The document content to analyze
        categories_to_analyze (list, optional): List of categories to analyze
    """
    # Default categories if none specified
    if categories_to_analyze is None:
        categories_to_analyze = ['business_summary', 'moat', 'financial', 'management']
    
    # Check for API key on each call, not relying on global variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        return {category: "<p>OpenAI API key not configured.</p>" for category in categories_to_analyze}
    
    # Log API key format for debugging (securely)
    key_prefix = api_key[:8] if len(api_key) > 8 else "too_short"
    logger.debug(f"Using OpenAI API key with prefix: {key_prefix}...")
    
    # Check if this is a project-based API key (sk-proj-*)
    if api_key.startswith("sk-proj-"):
        logger.info("Detected project-based API key (sk-proj-*)")
    
    insights = {}
    
    # Check API usage limits before proceeding
    from models import ApiUsage  # Import here to avoid circular imports
    usage_status = ApiUsage.check_usage_limits()
    if usage_status["usage_percent"] > 95:
        logger.warning(f"API usage at {usage_status['usage_percent']:.1f}% of budget, refusing to process")
        return {
            category: "<p>API usage limit reached. Please try again later or contact administrator.</p>"
            for category in categories_to_analyze
        }
    
    # Optimize the content to reduce token usage
    optimized_content = optimize_content_for_analysis(content)
    
    try:
        # Process only the requested insight categories
        for category in categories_to_analyze:
            # Skip if the category doesn't have a template
            if category not in PROMPT_TEMPLATES:
                logger.warning(f"No template found for category: {category}")
                continue
                
            prompt_template = PROMPT_TEMPLATES[category]
            try:
                # Fill the prompt template with optimized content
                prompt = prompt_template.format(content=optimized_content)
                
                # Make OpenAI API call
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                client = get_openai_client()
                if not client:
                    error_msg = "OpenAI API key not configured or invalid"
                    logger.error(error_msg)
                    
                    # Check if Hugging Face is available as fallback
                    if os.environ.get("HUGGINGFACE_API_KEY"):
                        logger.info("Attempting to fall back to Hugging Face for this category")
                        try:
                            from services.open_source_ai import analyze_with_prompt
                            fallback_result = analyze_with_prompt(optimized_content, prompt_template.format(content=optimized_content[:10000]))
                            if "<p>Error calling AI service" not in fallback_result:
                                logger.info(f"Successfully used Hugging Face as fallback for {category}")
                                insights[category] = fallback_result
                                continue
                        except Exception as hf_error:
                            logger.error(f"Hugging Face fallback also failed: {str(hf_error)}")
                    
                    raise Exception(error_msg)
                
                # Implement a retry mechanism for transient errors
                max_retries = 2
                backoff_time = 1  # Start with 1 second backoff
                
                for retry in range(max_retries + 1):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "You are an AI assistant that helps analyze company documents using value investing principles. Your answers should be concise and factual."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,  # Lower temperature for more focused responses
                            max_tokens=800    # Shorter responses
                        )
                        
                        # Extract the insight content from response
                        insight_content = response.choices[0].message.content
                        insights[category] = insight_content
                        
                        # If we get here, the request was successful, break out of retry loop
                        if retry > 0:
                            logger.info(f"Successfully completed request for {category} after {retry} retries")
                        break
                        
                    except Exception as retry_error:
                        error_str = str(retry_error).lower()
                        
                        # Check if this is a retryable error
                        is_retryable = any(term in error_str for term in 
                                            ["timeout", "rate limit", "ratelimit", "capacity", 
                                             "overloaded", "busy", "connection", "network", "500"])
                        
                        if retry < max_retries and is_retryable:
                            logger.warning(f"Retryable error on attempt {retry+1}/{max_retries+1}: {str(retry_error)}")
                            
                            # Exponential backoff
                            import time
                            time.sleep(backoff_time)
                            backoff_time *= 2  # Double the backoff time for next retry
                            
                            continue
                        else:
                            # Either we've exhausted retries or it's a non-retryable error
                            if retry == max_retries:
                                logger.error(f"Failed after {max_retries} retries: {str(retry_error)}")
                            else:
                                logger.error(f"Non-retryable error: {str(retry_error)}")
                            
                            # Try to extract more specific error info
                            error_type = "Unknown error"
                            if "authentication" in error_str or "auth" in error_str:
                                error_type = "Authentication error: check your API key"
                            elif "rate limit" in error_str:
                                error_type = "Rate limit exceeded"
                            elif "quota" in error_str or "billing" in error_str:
                                error_type = "Quota exceeded: check billing"
                            elif "invalid" in error_str and "model" in error_str:
                                error_type = "Invalid model: GPT-4o may not be available"
                            
                            raise Exception(f"{error_type}: {str(retry_error)}")
                
                # Log API usage
                try:
                    from models import ApiUsage, db
                    api_usage = ApiUsage(
                        api_name="openai",
                        document_id=None,  # Will be updated later in document processor
                        prompt_tokens=len(prompt) // 4,
                        completion_tokens=len(insight_content) // 4,
                        estimated_cost_usd=ApiUsage.calculate_openai_cost(len(prompt) // 4, len(insight_content) // 4),
                        model_name="gpt-4o",
                        request_successful=True
                    )
                    db.session.add(api_usage)
                    db.session.commit()
                except Exception as usage_error:
                    logger.error(f"Error recording API usage: {str(usage_error)}")
                
                logger.info(f"Successfully generated {category} insight with OpenAI")
                
            except Exception as e:
                logger.error(f"Error generating {category} insight with OpenAI: {str(e)}")
                # Record failed API usage
                try:
                    from models import ApiUsage, db
                    api_usage = ApiUsage(
                        api_name="openai",
                        document_id=None,
                        prompt_tokens=0,
                        completion_tokens=0,
                        estimated_cost_usd=0.0,
                        model_name="gpt-4o",
                        request_successful=False,
                        error_message=str(e)
                    )
                    db.session.add(api_usage)
                    db.session.commit()
                except Exception as usage_error:
                    logger.error(f"Error recording failed API usage: {str(usage_error)}")
                
                # Provide a fallback message for failed insights
                insights[category] = f"<p>Unable to generate {category} insight. Error: {str(e)}</p>"
    
    except Exception as e:
        logger.error(f"Error in content preprocessing: {str(e)}")
        # Fallback to a simpler approach if summarization fails
        for category in categories_to_analyze:
            # Skip if the category doesn't have a template
            if category not in PROMPT_TEMPLATES:
                logger.warning(f"No template found for category: {category}")
                continue
                
            prompt_template = PROMPT_TEMPLATES[category]
            try:
                # Use a much smaller content sample for fallback
                prompt = prompt_template.format(content=content[:5000])
                
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                client = get_openai_client(validate=False)  # Skip validation for fallback to reduce API calls
                if not client:
                    # Check if Hugging Face is available as fallback
                    if os.environ.get("HUGGINGFACE_API_KEY"):
                        logger.info(f"Attempting to use Hugging Face as final fallback for {category}")
                        try:
                            from services.open_source_ai import analyze_with_prompt
                            fallback_result = analyze_with_prompt(content[:7000], prompt_template.format(content=content[:7000]))
                            if "<p>Error calling AI service" not in fallback_result:
                                logger.info(f"Successfully used Hugging Face as final fallback for {category}")
                                insights[category] = fallback_result
                                continue
                        except Exception as hf_error:
                            logger.error(f"Hugging Face fallback also failed: {str(hf_error)}")
                    
                    raise Exception("OpenAI API key not configured or invalid")
                
                # Use a simplified retry mechanism for the fallback path
                max_retries = 1
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an AI assistant that helps analyze company documents using value investing principles."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=800
                    )
                    
                    insights[category] = response.choices[0].message.content
                    logger.info(f"Generated {category} insight with fallback method")
                
                except Exception as e:
                    logger.error(f"OpenAI fallback failed: {str(e)}")
                    
                    # If OpenAI fallback failed, try Hugging Face as a final resort
                    if os.environ.get("HUGGINGFACE_API_KEY"):
                        logger.info(f"Attempting emergency Hugging Face fallback for {category}")
                        try:
                            from services.open_source_ai import analyze_with_prompt
                            fallback_result = analyze_with_prompt(content[:7000], prompt_template.format(content=content[:7000]))
                            if "<p>Error calling AI service" not in fallback_result:
                                logger.info(f"Successfully used Hugging Face as emergency fallback for {category}")
                                insights[category] = fallback_result
                            else:
                                raise Exception("Hugging Face emergency fallback also failed")
                        except Exception as hf_error:
                            logger.error(f"Hugging Face emergency fallback failed: {str(hf_error)}")
                            insights[category] = f"<p>Unable to generate {category} insight after multiple fallback attempts. Please try again later.</p>"
                    else:
                        insights[category] = f"<p>Unable to generate {category} insight. Error: {str(e)}</p>"
                
            except Exception as e2:
                logger.error(f"Error in fallback generation for {category}: {str(e2)}")
                insights[category] = f"<p>Unable to generate {category} insight. Error: {str(e2)}</p>"
    
    return insights

def generate_insights_with_huggingface(content, categories_to_analyze=None):
    """
    Generate insights using Hugging Face's API
    
    Args:
        content (str): The document content to analyze
        categories_to_analyze (list, optional): List of categories to analyze
    """
    if categories_to_analyze is None:
        categories_to_analyze = ['business_summary', 'moat', 'financial', 'management']
        
    if not os.environ.get("HUGGINGFACE_API_KEY"):
        return {category: "<p>Hugging Face API key not configured.</p>" for category in categories_to_analyze}
    
    # Import the Hugging Face specific implementation
    try:
        from services.open_source_ai import generate_insights_with_huggingface as hf_generate
        
        # For now, we'll just pass the content and model - we'll need to update open_source_ai to handle categories
        # This would require a more extensive refactoring of that module
        insights = hf_generate(content, HUGGINGFACE_MODEL)
        
        # Filter to only include the requested categories
        filtered_insights = {}
        for category in categories_to_analyze:
            if category in insights:
                filtered_insights[category] = insights[category]
            elif category in PROMPT_TEMPLATES:
                # If the category is in the prompt templates but not in the insights,
                # we need to generate it specifically
                try:
                    from services.open_source_ai import analyze_with_prompt
                    prompt = PROMPT_TEMPLATES[category].format(content=content[:10000])  # Limit content size
                    result = analyze_with_prompt(content, prompt, HUGGINGFACE_MODEL)
                    filtered_insights[category] = result
                    logger.info(f"Generated additional {category} insight with Hugging Face")
                except Exception as e:
                    logger.error(f"Error generating {category} insight with Hugging Face: {str(e)}")
                    filtered_insights[category] = f"<p>Unable to generate {category} insight. Error: {str(e)}</p>"
                
        return filtered_insights
    except ImportError:
        logger.error("Failed to import open_source_ai module")
        return {category: "<p>Hugging Face integration not available.</p>" for category in categories_to_analyze}
    except Exception as e:
        logger.error(f"Error generating insights with Hugging Face: {str(e)}")
        return {category: f"<p>Hugging Face processing error: {str(e)}</p>" for category in categories_to_analyze}