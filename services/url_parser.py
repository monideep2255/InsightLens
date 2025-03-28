import requests
import logging
import trafilatura
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def extract_url_content(url):
    """
    Extract content from a URL using Trafilatura
    Returns a string containing the extracted text
    """
    try:
        # Validate URL
        validate_url(url)
        
        # Fetch content from URL
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Failed to fetch content from URL: {url}")
        
        # Extract main text content
        text = trafilatura.extract(downloaded)
        if not text or len(text.strip()) < 100:
            raise ValueError("Insufficient content extracted from the URL")
        
        logger.info(f"Successfully extracted content from URL: {url}")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting content from URL {url}: {str(e)}")
        raise Exception(f"Failed to extract content from URL: {str(e)}")

def validate_url(url):
    """
    Validate that the URL is properly formatted and accessible
    """
    # Check URL format
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL format")
        
        # Check that URL scheme is http or https
        if result.scheme not in ['http', 'https']:
            raise ValueError("URL must use HTTP or HTTPS protocol")
        
    except Exception as e:
        raise ValueError(f"URL validation error: {str(e)}")
    
    # Check URL accessibility
    try:
        response = requests.head(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"URL is not accessible: {str(e)}")
