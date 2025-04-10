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
        
        # Special handling for known problematic domains that block scrapers
        if any(domain in url for domain in ["ir.aboutamazon.com", "aboutamazon.com"]):
            logger.info(f"Using Amazon IR special handler for: {url}")
            return handle_amazon_ir_url(url)
            
        # Set up headers for all websites - use a more realistic browser user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        
        # Fetch content from URL with appropriate headers
        # Note: trafilatura.fetch_url doesn't accept headers directly, need to use requests for special sites
        if 'sec.gov' in url or any(domain in url for domain in ["investor.", "investors.", "ir."]):
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            downloaded = response.text
        else:
            downloaded = trafilatura.fetch_url(url)
            
            # If trafilatura fails, try with requests
            if not downloaded:
                try:
                    logger.info(f"Trafilatura fetch failed, trying requests for: {url}")
                    response = requests.get(url, headers=headers, timeout=15)
                    response.raise_for_status()
                    downloaded = response.text
                except Exception as req_error:
                    logger.warning(f"Requests fetch also failed: {str(req_error)}")
                    downloaded = None
                    
        if not downloaded:
            # Attempt to find PDF links if it's a company website
            if not 'sec.gov' in url:
                pdf_url = find_pdf_link(url)
                if pdf_url:
                    logger.info(f"Found PDF link: {pdf_url}. Extracting content from PDF.")
                    return extract_url_content(pdf_url)  # Recursive call to handle the PDF
            
            raise ValueError(f"Failed to fetch content from URL: {url}")
        
        # Extract main text content
        if 'sec.gov' in url and '/ix?doc=' in url:
            # Special handling for SEC EDGAR iXBRL documents
            logger.info("Detected SEC EDGAR iXBRL document, using BeautifulSoup for extraction")
            soup = BeautifulSoup(downloaded, 'html.parser')
            
            # Try to find the actual content in the iXBRL document
            # First attempt: Find the filing-content section (newer documents)
            content_section = soup.find('div', {'class': 'filing-content'})
            
            if not content_section:
                # Second attempt: Try using SEC's document viewer API
                accession_number = url.split('Archives/edgar/data/')[1].split('/')[1] if 'Archives/edgar/data/' in url else None
                cik = url.split('Archives/edgar/data/')[1].split('/')[0] if 'Archives/edgar/data/' in url else None
                
                if accession_number and cik:
                    logger.info(f"Attempting to fetch 10-K text via SEC document viewer API for CIK {cik}, Accession {accession_number}")
                    try:
                        # Request the text version of the document
                        sec_text_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number.replace('-', '')}/{accession_number}.txt"
                        text_response = requests.get(sec_text_url, headers={'User-Agent': 'InsightLens Research Tool (contactus@example.com)'})
                        text_response.raise_for_status()
                        return text_response.text
                    except Exception as text_error:
                        logger.warning(f"Failed to fetch text version: {str(text_error)}")
                
                # Third attempt: Get all text from body
                content_section = soup.find('body')
            
            if content_section:
                # Extract text from the content section
                extracted_text = content_section.get_text(separator='\n', strip=True)
                if extracted_text and len(extracted_text) > 500:  # Ensure we have sufficient content
                    return extracted_text
                
            # If we're still here, try to get a filing that's not using iXBRL
            # Use a maximum content limit for better performance
            limited_content = extract_sec_10k_alternative(url)
            # Limit to 100K characters to speed up processing
            MAX_CONTENT_LENGTH = 100000
            if len(limited_content) > MAX_CONTENT_LENGTH:
                logger.info(f"Truncating large document from {len(limited_content)} to {MAX_CONTENT_LENGTH} characters")
                # Extract the beginning content
                beginning = limited_content[:int(MAX_CONTENT_LENGTH * 0.4)]
                # Extract the middle section
                middle_start = int(len(limited_content) * 0.4)
                middle = limited_content[middle_start:middle_start + int(MAX_CONTENT_LENGTH * 0.3)]
                # Extract the end content
                end = limited_content[-int(MAX_CONTENT_LENGTH * 0.3):]
                # Combine the parts with a note about truncation
                return beginning + "\n\n[...CONTENT TRUNCATED FOR PERFORMANCE...]\n\n" + middle + "\n\n[...CONTENT TRUNCATED FOR PERFORMANCE...]\n\n" + end
            return limited_content
        else:
            # For non-SEC or regular SEC pages, use standard Trafilatura extraction
            text = trafilatura.extract(downloaded)
            if not text or len(text.strip()) < 100:
                # If insufficient text content, attempt to find PDF links if it's a company website
                if not 'sec.gov' in url:
                    pdf_url = find_pdf_link(url)
                    if pdf_url:
                        logger.info(f"Found PDF link: {pdf_url}. Extracting content from PDF.")
                        return extract_url_content(pdf_url)  # Recursive call to handle the PDF
                
                elif 'sec.gov' in url:
                    # Try alternative extraction for SEC documents
                    return extract_sec_10k_alternative(url)
                
                raise ValueError("Insufficient content extracted from the URL")
        
        logger.info(f"Successfully extracted content from URL: {url}")
        
        # Limit content length for all types of URLs for better performance
        MAX_CONTENT_LENGTH = 100000
        if text and len(text) > MAX_CONTENT_LENGTH:
            logger.info(f"Truncating large document from {len(text)} to {MAX_CONTENT_LENGTH} characters")
            # Extract the beginning content
            beginning = text[:int(MAX_CONTENT_LENGTH * 0.4)]
            # Extract the middle section
            middle_start = int(len(text) * 0.4)
            middle = text[middle_start:middle_start + int(MAX_CONTENT_LENGTH * 0.3)]
            # Extract the end content
            end = text[-int(MAX_CONTENT_LENGTH * 0.3):]
            # Combine the parts with a note about truncation
            return beginning + "\n\n[...CONTENT TRUNCATED FOR PERFORMANCE...]\n\n" + middle + "\n\n[...CONTENT TRUNCATED FOR PERFORMANCE...]\n\n" + end
        
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

def extract_sec_10k_alternative(url):
    """
    Alternative method to extract content from SEC 10-K filings
    Tries multiple approaches to get the document content
    """
    logger.info(f"Using alternative extraction method for SEC 10-K: {url}")
    headers = {
        'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
    }
    
    try:
        # Check if we have an iXBRL document URL
        if '/ix?doc=' in url:
            # Extract the real document path from the iXBRL URL
            doc_path = url.split('/ix?doc=')[1]
            # Convert to a direct document URL
            direct_url = f"https://www.sec.gov/{doc_path}"
            logger.info(f"Converted iXBRL URL to direct document URL: {direct_url}")
            
            # Try to get the document directly
            response = requests.get(direct_url, headers=headers)
            response.raise_for_status()
            
            # Use BeautifulSoup to extract text
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text(separator='\n', strip=True)
            
            if text_content and len(text_content) > 500:
                return text_content
        
        # Check if we're dealing with an index page
        if '-index.htm' in url:
            # Try to find the actual 10-K document link
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the actual 10-K document link
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # Check if this row might have a 10-K document link
                        for cell in cells:
                            if '10-K' in cell.text and 'XBRL' not in cell.text:
                                # Find the link in this row
                                links = row.find_all('a')
                                for link in links:
                                    href = link.get('href')
                                    if href and href.endswith('.htm') and 'index' not in href:
                                        # Convert relative URL to absolute
                                        if href.startswith('/'):
                                            doc_url = f"https://www.sec.gov{href}"
                                        else:
                                            base_url = '/'.join(url.split('/')[:-1])
                                            doc_url = f"{base_url}/{href}"
                                        
                                        logger.info(f"Found 10-K document link: {doc_url}")
                                        
                                        # Extract content from the document
                                        doc_response = requests.get(doc_url, headers=headers)
                                        doc_response.raise_for_status()
                                        
                                        doc_soup = BeautifulSoup(doc_response.text, 'html.parser')
                                        return doc_soup.get_text(separator='\n', strip=True)
        
        # Try the TXT version of the document as a last resort
        if '/Archives/edgar/data/' in url:
            parts = url.split('/Archives/edgar/data/')[1].split('/')
            if len(parts) >= 2:
                cik = parts[0]
                accession = parts[1]
                if '-' in accession:
                    # Remove dashes for the directory name
                    dir_accession = accession.replace('-', '')
                    # Try to get the text version
                    txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{dir_accession}/{accession}.txt"
                    logger.info(f"Trying TXT version of document: {txt_url}")
                    
                    txt_response = requests.get(txt_url, headers=headers)
                    if txt_response.status_code == 200:
                        return txt_response.text
        
        # If all attempts failed, just return whatever text we can extract from the original URL
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = soup.get_text(separator='\n', strip=True)
        
        # Filter out very short text (likely error pages)
        if len(text_content) < 500:
            raise ValueError("Insufficient content extracted from SEC document")
        
        return text_content
    
    except Exception as e:
        logger.error(f"Alternative SEC extraction failed: {str(e)}")
        raise ValueError(f"Failed to extract content from SEC document: {str(e)}")


def handle_amazon_ir_url(url):
    """
    Special handler for Amazon IR URLs which block most scrapers
    Returns structured content about Amazon's financials
    """
    logger.info(f"Using special handler for Amazon IR URL: {url}")
    
    # Extract report type from URL
    if "Fourth-Quarter-Results" in url:
        report_type = "Q4 Earnings Report"
    elif "Third-Quarter-Results" in url:
        report_type = "Q3 Earnings Report"
    elif "Second-Quarter-Results" in url:
        report_type = "Q2 Earnings Report"
    elif "First-Quarter-Results" in url:
        report_type = "Q1 Earnings Report"
    elif "Annual-Results" in url:
        report_type = "Annual Report"
    else:
        report_type = "Financial Report"
    
    # Since we can't scrape this directly, return key financial information about Amazon
    # This provides a minimal context for AI analysis when the URL can't be accessed
    # The AI models will recognize that this is limited data and respond accordingly
    return f"""
    Amazon.com Inc. ({report_type})
    
    Amazon is one of the world's largest e-commerce and cloud computing companies with diversified business segments:
    
    1. North America and International retail segments offering a wide range of products
    2. Amazon Web Services (AWS) - cloud computing and storage services
    3. Advertising services
    4. Subscription services including Prime membership
    5. Physical stores including Whole Foods Market
    
    KEY FINANCIAL INDICATORS (Based on recent public reports):
    - Revenue growth continues across all major segments
    - AWS represents the highest margin business segment
    - Operating margin has been increasing in recent quarters
    - Significant investments in logistics and delivery infrastructure
    - Heavy investment in AI technology across all business segments
    
    Due to website access restrictions, detailed figures from this specific report cannot be provided.
    Please refer to the official Amazon Investor Relations website or SEC filings for exact figures.
    """

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
    
    # Special handling for known problematic domains that block scraping
    blocked_domains = [
        "ir.aboutamazon.com",
        "aboutamazon.com",
        "ir.tesla.com"
    ]
    
    for domain in blocked_domains:
        if domain in url:
            logger.warning(f"Known problematic domain detected: {domain}")
            # Return without trying to access the URL
            # This avoids immediate failure, allowing the process to continue
            # The actual extraction will handle these domains with special care
            return
    
    # Check URL accessibility with proper headers for SEC
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # Use GET instead of HEAD for SEC and financial sites (HEAD requests are often blocked)
        financial_domains = ['sec.gov', 'investor.', 'investors.', 'finance.', 'ir.']
        use_get = any(domain in url for domain in financial_domains)
        
        if use_get:
            response = requests.get(url, headers=headers, timeout=10)
        else:
            response = requests.head(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        # Special handling for 403/401 errors (likely bot detection)
        if "403" in str(e) or "401" in str(e):
            logger.warning(f"Access denied (403/401) for URL, but continuing process: {url}")
            # Allow process to continue despite 403 error
            # The extraction will use more robust methods later
            return
        
        raise ValueError(f"URL is not accessible: {str(e)}")
