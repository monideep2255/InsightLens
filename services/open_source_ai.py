import os
import json
import requests
import logging

logger = logging.getLogger(__name__)

# Note: You'll need to sign up for a free Hugging Face account 
# and get an API key at https://huggingface.co/settings/tokens
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

# Model options (these are examples of available open source models)
# You can find more at https://huggingface.co/models
MODEL_OPTIONS = {
    "deepseek": "deepseek-ai/deepseek-coder-33b-instruct",
    "llama3": "meta-llama/Llama-3-8b-chat-hf",  # Requires accepting terms of use
    "mistral": "mistralai/Mixtral-8x7B-Instruct-v0.1"
}

def generate_insights_with_huggingface(content, model_name="mistral"):
    """
    Generate insights using Hugging Face Inference API with open source models
    
    Args:
        content (str): The document content to analyze
        model_name (str): Key from MODEL_OPTIONS to select which model to use
    
    Returns:
        dict: Structured insights from the document
    """
    if not HUGGINGFACE_API_KEY:
        raise ValueError("Missing HUGGINGFACE_API_KEY environment variable")
    
    model = MODEL_OPTIONS.get(model_name)
    if not model:
        raise ValueError(f"Unknown model: {model_name}. Available options: {list(MODEL_OPTIONS.keys())}")
    
    # Build the prompt
    prompt = f"""
    You are a financial analysis expert. Analyze the following document content and extract structured insights 
    about the company being described. Focus on value investing principles (Benjamin Graham/Warren Buffett approach).
    
    Please structure your response as a JSON object with these categories:
    
    1. business_summary: A concise overview of what the company does, its industry, products/services.
    2. moat: Any competitive advantages, barriers to entry, brand strength, etc.
    3. financial: Key insights about revenue, profit margins, debt levels, cash flow.
    4. management: Leadership quality, capital allocation skills, insider ownership.
    
    Document content:
    {content[:15000]}  # Truncating content to fit within token limits
    
    Respond ONLY with the JSON object containing these four categories.
    """
    
    # API call to Hugging Face
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.3,
            "top_p": 0.9,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # Parse the response - format varies by model
        try:
            result = response.json()
            
            # Extract the generated text (format depends on the model)
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and "generated_text" in result[0]:
                    raw_output = result[0]["generated_text"]
                elif isinstance(result[0], str):
                    raw_output = result[0]
                else:
                    # Convert unknown object to string representation
                    raw_output = str(result[0])
            elif isinstance(result, dict) and "generated_text" in result:
                raw_output = result["generated_text"]
            elif isinstance(result, str):
                raw_output = result
            else:
                # Convert unknown object to string representation
                raw_output = str(result)
        except ValueError as json_error:
            # If the response isn't valid JSON, use the raw text
            logger.warning(f"Failed to parse JSON response: {str(json_error)}")
            raw_output = response.text
        
        # Extract JSON content
        try:
            # Check if raw_output is a string before trying to find JSON in it
            if isinstance(raw_output, str):
                start_idx = raw_output.find('{')
                end_idx = raw_output.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = raw_output[start_idx:end_idx]
                    try:
                        insights_data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # If the extracted JSON string is invalid, try to parse the entire response
                        logger.warning("Could not parse extracted JSON string, trying entire response")
                        insights_data = json.loads(raw_output)
                else:
                    # Fallback: try to parse entire response as JSON
                    insights_data = json.loads(raw_output)
            elif isinstance(raw_output, dict):
                # If it's already a dict, use it directly
                insights_data = raw_output
            else:
                # Convert to string and then try to parse as JSON
                raw_output_str = str(raw_output)
                logger.warning(f"Unexpected type for raw_output: {type(raw_output)}. Converting to string.")
                insights_data = json.loads(raw_output_str)
            
            # Ensure all required categories exist and convert any nested dictionaries to strings
            insights = {}
            required_keys = ['business_summary', 'moat', 'financial', 'management']
            
            for key in required_keys:
                if key not in insights_data:
                    insights[key] = "No information available"
                else:
                    # Check if the value is a dictionary and convert to string if needed
                    if isinstance(insights_data[key], dict):
                        # Format the nested dictionary into a nice HTML string
                        formatted_content = "<div class='nested-content'>"
                        for subkey, subvalue in insights_data[key].items():
                            formatted_content += f"<h4>{subkey.title()}</h4><p>{subvalue}</p>"
                        formatted_content += "</div>"
                        insights[key] = formatted_content
                    else:
                        insights[key] = insights_data[key]
            
            # Add any additional keys that weren't in required_keys
            for key in insights_data:
                if key not in required_keys:
                    if isinstance(insights_data[key], dict):
                        # Format the nested dictionary into a nice HTML string
                        formatted_content = "<div class='nested-content'>"
                        for subkey, subvalue in insights_data[key].items():
                            formatted_content += f"<h4>{subkey.title()}</h4><p>{subvalue}</p>"
                        formatted_content += "</div>"
                        insights[key] = formatted_content
                    else:
                        insights[key] = insights_data[key]
            
            return insights
            
        except json.JSONDecodeError:
            # If we can't parse JSON, create a structured format from the raw text
            return {
                'business_summary': "Error parsing model output. Please try again.",
                'moat': "Error parsing model output. Please try again.",
                'financial': "Error parsing model output. Please try again.",
                'management': "Error parsing model output. Please try again."
            }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return {
            'business_summary': "Error calling AI service. Please try again later.",
            'moat': "Error calling AI service. Please try again later.",
            'financial': "Error calling AI service. Please try again later.",
            'management': "Error calling AI service. Please try again later."
        }
        
def analyze_with_prompt(content, prompt_template, model_name="mistral"):
    """
    Generate insights using a custom prompt template with Hugging Face models
    
    Args:
        content (str): The document content to analyze
        prompt_template (str): The prompt template to use
        model_name (str): Key from MODEL_OPTIONS to select which model to use
        
    Returns:
        str: Raw HTML content with the analysis results
    """
    if not HUGGINGFACE_API_KEY:
        return "<p>Hugging Face API key not configured.</p>"
    
    # Get the model ID from our options
    model = MODEL_OPTIONS.get(model_name)
    if not model:
        logger.error(f"Unknown model: {model_name}")
        return "<p>Invalid model configuration.</p>"
    
    # Prepare the content to analyze (truncate if needed)
    truncated_content = content[:15000]  # Limit length to avoid exceeding token limits
    
    # Format the prompt with the truncated content
    prompt = prompt_template.format(content=truncated_content)
    
    # API call to Hugging Face
    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1500,  # Longer output for comprehensive analysis
            "temperature": 0.3,
            "top_p": 0.9,
            "return_full_text": False
        }
    }
    
    # Implement a retry mechanism with exponential backoff
    max_retries = 2
    backoff_time = 1  # Start with 1 second
    
    for retry in range(max_retries + 1):
        try:
            # Add timeout to avoid hanging requests
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            # Parse the response - format varies by model
            try:
                result = response.json()
                
                # Extract the generated text (format depends on the model)
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict) and "generated_text" in result[0]:
                        raw_output = result[0]["generated_text"]
                    elif isinstance(result[0], str):
                        raw_output = result[0]
                    else:
                        # Convert unknown object to string representation
                        raw_output = str(result[0])
                elif isinstance(result, dict) and "generated_text" in result:
                    raw_output = result["generated_text"]
                elif isinstance(result, str):
                    raw_output = result
                else:
                    # Convert unknown object to string representation
                    raw_output = str(result)
            except ValueError as json_error:
                # If the response isn't valid JSON, use the raw text
                logger.warning(f"Failed to parse JSON response: {str(json_error)}")
                raw_output = response.text
            
            # Check for model-specific error messages in the output
            error_indicators = ["error", "invalid", "failed", "quota exceeded", "rate limit"]
            if isinstance(raw_output, str) and any(indicator in raw_output.lower() for indicator in error_indicators):
                logger.warning(f"Possible error in model output: {raw_output[:100]}...")
                if retry < max_retries:
                    logger.info(f"Retrying due to error in model output (attempt {retry+1}/{max_retries+1})")
                    import time
                    time.sleep(backoff_time)
                    backoff_time *= 2
                    continue
            
            # Check if the result contains HTML, if not, wrap it in paragraph tags
            if "<h" in raw_output or "<p>" in raw_output:
                return raw_output
            else:
                return f"<p>{raw_output}</p>"
            
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout on attempt {retry+1}/{max_retries+1}")
            if retry < max_retries:
                import time
                time.sleep(backoff_time)
                backoff_time *= 2
                continue
            else:
                logger.error("All retries failed due to timeout")
                return "<p>Error: The AI service took too long to respond. Please try again later.</p>"
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else 0
            logger.warning(f"HTTP error {status_code} on attempt {retry+1}/{max_retries+1}: {str(e)}")
            
            # Check if it's a retryable error (server errors, rate limits)
            if ((isinstance(status_code, int) and (500 <= status_code <= 599 or status_code == 429)) 
                and retry < max_retries):
                import time
                wait_time = backoff_time
                
                # If we get a rate limit response, use the Retry-After header if available
                if status_code == 429 and hasattr(e, 'response') and 'Retry-After' in e.response.headers:
                    try:
                        wait_time = int(e.response.headers['Retry-After'])
                        logger.info(f"Using Retry-After header: waiting {wait_time} seconds")
                    except (ValueError, TypeError):
                        pass
                
                logger.info(f"Retrying in {wait_time} seconds")
                time.sleep(wait_time)
                backoff_time *= 2
                continue
            else:
                # Non-retryable error or out of retries
                logger.error(f"HTTP error {status_code}: {str(e)}")
                error_type = "rate limit exceeded" if status_code == 429 else f"HTTP error {status_code}"
                return f"<p>Error calling AI service: {error_type}. Please try again later.</p>"
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error during custom prompt analysis: {e}")
            
            # Check if it's a connection error that might be temporary
            is_connection_error = any(term in str(e).lower() for term in ["connection", "network", "dns", "timeout", "read timed out"])
            if is_connection_error and retry < max_retries:
                logger.info(f"Connection error, retrying (attempt {retry+1}/{max_retries+1})")
                import time
                time.sleep(backoff_time)
                backoff_time *= 2
                continue
            
            return f"<p>Error calling AI service: {str(e)}. Please try again later.</p>"
        
        except Exception as unexpected_error:
            # For any other unexpected errors
            logger.error(f"Unexpected error during API request: {str(unexpected_error)}")
            return f"<p>An unexpected error occurred while processing your request. Please try again later.</p>"
    
    # If we get here, all retries failed
    return "<p>Unable to get a valid response from the AI service after multiple attempts. Please try again later.</p>"