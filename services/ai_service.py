import os
import json
import logging
import requests

# Optional import of OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# AI Model Configuration - read from environment
AI_MODEL_TYPE = os.environ.get("AI_MODEL_TYPE", "openai").lower()  # Default to OpenAI if not specified
HUGGINGFACE_MODEL = os.environ.get("HUGGINGFACE_MODEL", "mistral")  # Default Hugging Face model

# Initialize OpenAI client if available and selected
if AI_MODEL_TYPE == "openai" and OPENAI_AVAILABLE:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        openai = OpenAI(api_key=OPENAI_API_KEY)
    else:
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

# Prompt templates
PROMPT_TEMPLATES = {
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

def generate_insights(content):
    """
    Generate structured insights from document content using the configured AI model
    Returns a dictionary mapping insight categories to their content
    """
    # Choose the appropriate model based on configuration
    if AI_MODEL_TYPE == "openai" and OPENAI_AVAILABLE:
        return generate_insights_with_openai(content)
    elif AI_MODEL_TYPE == "huggingface":
        return generate_insights_with_huggingface(content)
    else:
        logger.error(f"Invalid AI model type: {AI_MODEL_TYPE}")
        return {
            'business_summary': "<p>AI model configuration error. Please check server logs.</p>",
            'moat': "<p>AI model configuration error. Please check server logs.</p>",
            'financial': "<p>AI model configuration error. Please check server logs.</p>",
            'management': "<p>AI model configuration error. Please check server logs.</p>"
        }

def generate_insights_with_openai(content):
    """
    Generate insights using OpenAI's API
    """
    if not OPENAI_API_KEY:
        return {category: "<p>OpenAI API key not configured.</p>" for category in PROMPT_TEMPLATES.keys()}
    
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
            summary_response = openai.chat.completions.create(
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
    
        # Process each insight category with its own prompt
        for category, prompt_template in PROMPT_TEMPLATES.items():
            try:
                # Fill the prompt template with optimized content
                prompt = prompt_template.format(content=content_to_analyze)
                
                # Make OpenAI API call
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                response = openai.chat.completions.create(
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
        for category, prompt_template in PROMPT_TEMPLATES.items():
            try:
                # Use a much smaller content sample for fallback
                prompt = prompt_template.format(content=content[:5000])
                
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                response = openai.chat.completions.create(
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

def generate_insights_with_huggingface(content):
    """
    Generate insights using Hugging Face's API
    """
    if not os.environ.get("HUGGINGFACE_API_KEY"):
        return {category: "<p>Hugging Face API key not configured.</p>" for category in PROMPT_TEMPLATES.keys()}
    
    # Create a more optimized process for Hugging Face
    
    # First, prepare optimized content
    MAX_CONTENT_LENGTH = 8000
    if len(content) > MAX_CONTENT_LENGTH:
        logger.info(f"Content is large ({len(content)} chars), creating optimized version for Hugging Face")
        # Extract the beginning content
        beginning = content[:int(MAX_CONTENT_LENGTH * 0.4)]
        # Extract the middle section
        middle_start = int(len(content) * 0.4)
        middle = content[middle_start:middle_start + int(MAX_CONTENT_LENGTH * 0.3)]
        # Extract the end content
        end = content[-int(MAX_CONTENT_LENGTH * 0.3):]
        # Combine the parts with a note about truncation
        optimized_content = beginning + "\n\n[...CONTENT TRUNCATED...]\n\n" + middle + "\n\n[...CONTENT TRUNCATED...]\n\n" + end
    else:
        optimized_content = content
    
    # Combine all prompts into a single comprehensive prompt for efficiency
    combined_prompt = """
    Analyze the following company document and extract structured insights using value investing principles.
    
    INSTRUCTIONS:
    - Keep your analysis very concise (1-2 sentences per section)
    - Focus only on facts found in the document, not general advice
    - Format as HTML sections with these exact headings:
    
    <h4>Business Summary</h4>
    [1-2 sentences on what the company does, its industry, and customers]
    
    <h4>Competitive Moat</h4>
    [1-2 sentences on any competitive advantages or barriers to entry]
    
    <h4>Financial Health</h4>
    [1-2 sentences on revenue, profitability, debt levels, cash flow]
    
    <h4>Management Analysis</h4>
    [1-2 sentences on leadership quality and capital allocation]
    
    DOCUMENT CONTENT:
    {content}
    """
    
    insights = {}
    
    try:
        # Select the model to use
        model_name = HUGGINGFACE_MODEL_OPTIONS.get(HUGGINGFACE_MODEL, HUGGINGFACE_MODEL_OPTIONS["mistral"])
        
        # Set up API call
        headers = {
            "Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        # Prepare the API call
        API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
        
        payload = {
            "inputs": combined_prompt.format(content=optimized_content[:6000]),  # Much smaller content limit for fast performance
            "parameters": {
                "max_new_tokens": 800,  # Shorter responses
                "temperature": 0.2,     # More focused responses
                "top_p": 0.85,          # More deterministic
                "return_full_text": False
            }
        }
        
        # Make the request
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            # Parse the response (format varies by model)
            try:
                result = response.json()
                
                # Extract the generated text (format depends on the model)
                if isinstance(result, list) and len(result) > 0:
                    if "generated_text" in result[0]:
                        raw_output = result[0]["generated_text"]
                    else:
                        raw_output = result[0]
                else:
                    raw_output = result
                
                # Extract sections from the HTML
                raw_html = raw_output if isinstance(raw_output, str) else str(raw_output)
                
                # Very basic HTML section extraction
                if "<h4>Business Summary</h4>" in raw_html:
                    # The model returned correctly formatted HTML sections
                    business_start = raw_html.find("<h4>Business Summary</h4>")
                    moat_start = raw_html.find("<h4>Competitive Moat</h4>")
                    financial_start = raw_html.find("<h4>Financial Health</h4>")
                    management_start = raw_html.find("<h4>Management Analysis</h4>")
                    
                    insights["business_summary"] = raw_html[business_start:moat_start].strip() if moat_start > 0 else "<p>Unable to extract business summary.</p>"
                    insights["moat"] = raw_html[moat_start:financial_start].strip() if financial_start > 0 else "<p>Unable to extract competitive moat information.</p>"
                    insights["financial"] = raw_html[financial_start:management_start].strip() if management_start > 0 else "<p>Unable to extract financial information.</p>"
                    insights["management"] = raw_html[management_start:].strip() if management_start > 0 else "<p>Unable to extract management information.</p>"
                else:
                    # Model didn't format as expected, use the entire output as business summary
                    logger.warning("Hugging Face model did not return expected HTML sections")
                    insights["business_summary"] = f"<p>{raw_html}</p>"
                    insights["moat"] = "<p>The model did not generate properly structured insights.</p>"
                    insights["financial"] = "<p>The model did not generate properly structured insights.</p>"
                    insights["management"] = "<p>The model did not generate properly structured insights.</p>"
                
                logger.info("Successfully generated insights with Hugging Face")
                
            except Exception as parsing_error:
                logger.error(f"Error parsing Hugging Face response: {str(parsing_error)}")
                for category in PROMPT_TEMPLATES.keys():
                    insights[category] = f"<p>Error parsing model response: {str(parsing_error)}</p>"
        else:
            logger.error(f"Hugging Face API error: {response.status_code} - {response.text}")
            for category in PROMPT_TEMPLATES.keys():
                insights[category] = f"<p>Hugging Face API error: {response.status_code}</p>"
                
    except Exception as e:
        logger.error(f"Error calling Hugging Face API: {str(e)}")
        for category in PROMPT_TEMPLATES.keys():
            insights[category] = f"<p>Error calling Hugging Face API: {str(e)}</p>"
    
    return insights
