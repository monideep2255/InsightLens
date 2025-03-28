import requests
import logging
import trafilatura
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def extract_url_content(url):
    """
    Extract content from a URL using Trafilatura
    Returns a string containing the extracted text
    """
    try:
        # Check if the URL points directly to a PDF
        if url.lower().endswith('.pdf'):
            # Handle PDF extraction
            from services.pdf_parser import extract_pdf_content
            import tempfile
            import os
            import requests
            
            # Create a temporary file to store the downloaded PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
                # Set up headers for SEC website
                headers = {}
                if 'sec.gov' in url:
                    headers = {
                        'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
                    }
                
                # Download the PDF
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()
                
                # Write the PDF to the temporary file
                for chunk in response.iter_content(chunk_size=8192):
                    temp.write(chunk)
            
            # Extract text from the PDF
            try:
                content = extract_pdf_content(temp.name)
                os.unlink(temp.name)  # Clean up the temporary file
                return content
            except Exception as pdf_error:
                os.unlink(temp.name)  # Clean up the temporary file
                raise pdf_error
        
        # Validate URL
        validate_url(url)
        
        # Set up headers for SEC website
        headers = None
        if 'sec.gov' in url:
            headers = {
                'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
            }
        
        # Fetch content from URL with appropriate headers
        downloaded = trafilatura.fetch_url(url, headers=headers)
        if not downloaded:
            # Attempt to find PDF links if it's a company website
            if not 'sec.gov' in url:
                pdf_url = find_pdf_link(url)
                if pdf_url:
                    logger.info(f"Found PDF link: {pdf_url}. Extracting content from PDF.")
                    return extract_url_content(pdf_url)  # Recursive call to handle the PDF
            
            raise ValueError(f"Failed to fetch content from URL: {url}")
        
        # Extract main text content
        text = trafilatura.extract(downloaded)
        if not text or len(text.strip()) < 100:
            # If insufficient text content, attempt to find PDF links if it's a company website
            if not 'sec.gov' in url:
                pdf_url = find_pdf_link(url)
                if pdf_url:
                    logger.info(f"Found PDF link: {pdf_url}. Extracting content from PDF.")
                    return extract_url_content(pdf_url)  # Recursive call to handle the PDF
            
            raise ValueError("Insufficient content extracted from the URL")
        
        logger.info(f"Successfully extracted content from URL: {url}")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting content from URL {url}: {str(e)}")
        raise Exception(f"Failed to extract content from URL: {str(e)}")


def find_pdf_link(url):
    """
    Attempt to find a PDF link (like an annual report) on a company's website
    Returns the URL of the PDF if found, None otherwise
    """
    try:
        headers = {
            'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for links to PDFs that might be annual reports
        annual_report_keywords = [
            'annual report', 'annual-report', 'annualreport', 
            '10-k', '10k', 'financial report', 'investor'
        ]
        
        for link in soup.find_all('a'):
            href = link.get('href')
            text = link.text.lower()
            
            if href and href.lower().endswith('.pdf'):
                # Check if the link text contains keywords related to annual reports
                if any(keyword in text for keyword in annual_report_keywords):
                    # Convert relative URL to absolute URL
                    if not href.startswith(('http://', 'https://')):
                        parsed_url = urlparse(url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        
                        if href.startswith('/'):
                            href = f"{base_url}{href}"
                        else:
                            directory = '/'.join(parsed_url.path.split('/')[:-1])
                            href = f"{base_url}{directory}/{href}"
                    
                    return href
        
        # If we didn't find any annual report specific PDFs, try to find any PDF
        for link in soup.find_all('a'):
            href = link.get('href')
            
            if href and href.lower().endswith('.pdf'):
                # Convert relative URL to absolute URL
                if not href.startswith(('http://', 'https://')):
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    
                    if href.startswith('/'):
                        href = f"{base_url}{href}"
                    else:
                        directory = '/'.join(parsed_url.path.split('/')[:-1])
                        href = f"{base_url}{directory}/{href}"
                
                return href
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding PDF link on {url}: {str(e)}")
        return None

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
    
    # Check URL accessibility with proper headers for SEC
    headers = {
        'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
    }
    
    try:
        # Use GET instead of HEAD for SEC (HEAD requests are often blocked)
        if 'sec.gov' in url:
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.head(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"URL is not accessible: {str(e)}")
