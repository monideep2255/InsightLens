import os
import json
import requests

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
        result = response.json()
        
        # Extract the generated text (format depends on the model)
        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                raw_output = result[0]["generated_text"]
            else:
                raw_output = result[0]
        else:
            raw_output = result
        
        # Extract JSON content
        try:
            # Try to find JSON in the response
            start_idx = raw_output.find('{')
            end_idx = raw_output.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = raw_output[start_idx:end_idx]
                insights = json.loads(json_str)
            else:
                # Fallback: try to parse entire response as JSON
                insights = json.loads(raw_output)
            
            # Ensure all required categories exist
            required_keys = ['business_summary', 'moat', 'financial', 'management']
            for key in required_keys:
                if key not in insights:
                    insights[key] = "No information available"
            
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
        print(f"API request error: {e}")
        return {
            'business_summary': "Error calling AI service. Please try again later.",
            'moat': "Error calling AI service. Please try again later.",
            'financial': "Error calling AI service. Please try again later.",
            'management': "Error calling AI service. Please try again later."
        }