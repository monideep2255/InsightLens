import os
import json
import logging
import requests
from services.new_prompt_templates import NEW_PROMPT_TEMPLATES

# Optional import of OpenAI
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# AI Model Configuration - read from environment
AI_MODEL_TYPE = os.environ.get("AI_MODEL_TYPE", "huggingface").lower()  # Default to Hugging Face
HUGGINGFACE_MODEL = os.environ.get("HUGGINGFACE_MODEL", "mistral")  # Default Hugging Face model

# Initialize OpenAI client functions
def get_openai_client():
    """Get an OpenAI client with the latest API key from environment variables"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        return None
    
    # Log API key format for debugging (securely)
    key_prefix = api_key[:8] if len(api_key) > 8 else "too_short"
    logger.debug(f"Initializing OpenAI client with API key starting with {key_prefix}...")
    
    # Directly set the API key in the openai module
    openai.api_key = api_key
    
    # Configuration for organization ID if present
    organization = os.environ.get("OPENAI_ORGANIZATION")
    if organization:
        logger.debug(f"Using organization ID: {organization}")
        openai.organization = organization
    
    # Log version info
    version_info = getattr(openai, "__version__", "unknown")
    logger.debug(f"OpenAI SDK version: {version_info}")
    
    # Create and return the client using module-level configuration
    try:
        client = OpenAI(api_key=api_key)
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
        return {category: "<p>OpenAI API key not configured.</p>" for category in PROMPT_TEMPLATES.keys()}
    
    # Log API key format for debugging (securely)
    key_prefix = api_key[:8] if len(api_key) > 8 else "too_short"
    logger.debug(f"Using OpenAI API key with prefix: {key_prefix}...")
    
    # Check if this is a project-based API key (sk-proj-*)
    if api_key.startswith("sk-proj-"):
        logger.info("Detected project-based API key (sk-proj-*)")
    
    insights = {}
    
    # Create a more optimized summarized version of the content
    try:
        # First, get a condensed version of the content for better efficiency
        MAX_ORIGINAL_CONTENT = 8000  # Limit initial content size
        truncated_content = content[:MAX_ORIGINAL_CONTENT]
        
        # If content is very large, get a summarized version first
        if len(content) > MAX_ORIGINAL_CONTENT:
            logger.info(f"Content is large ({len(content)} chars), creating summary first")
            # Create a brief summary for the main points of the document
            summary_prompt = f"""
            Summarize the key business points in this document in 1000 words or less.
            Focus on extracting facts about:
            1. The company's business model and products/services
            2. Market position and competitive advantages
            3. Financial metrics mentioned
            4. Management statements and strategy
            
            DOCUMENT CONTENT:
            {truncated_content}
            """
            
            # Generate a summary first
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
            
            # Create a combined document with both summary and samples from the original
            # This gives the AI both a high-level view and specific details
            content_to_analyze = f"""
            DOCUMENT SUMMARY:
            {summary}
            
            BEGINNING OF DOCUMENT:
            {content[:2500]}
            
            MIDDLE OF DOCUMENT:
            {content[len(content)//2-1000:len(content)//2+1000] if len(content) > 5000 else ""}
            
            END OF DOCUMENT:
            {content[-2500:] if len(content) > 5000 else ""}
            """
        else:
            content_to_analyze = truncated_content
    
        # Process only the requested insight categories
        for category in categories_to_analyze:
            # Skip if the category doesn't have a template
            if category not in PROMPT_TEMPLATES:
                logger.warning(f"No template found for category: {category}")
                continue
                
            prompt_template = PROMPT_TEMPLATES[category]
            try:
                # Fill the prompt template with optimized content
                prompt = prompt_template.format(content=content_to_analyze)
                
                # Make OpenAI API call
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                client = get_openai_client()
                if not client:
                    raise Exception("OpenAI API key not configured or invalid")
                    
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
                
                logger.info(f"Successfully generated {category} insight with OpenAI")
                
            except Exception as e:
                logger.error(f"Error generating {category} insight with OpenAI: {str(e)}")
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
                client = get_openai_client()
                if not client:
                    raise Exception("OpenAI API key not configured or invalid")
                    
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