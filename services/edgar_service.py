import requests
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def search_company(company_name):
    """
    Search for a company in the SEC EDGAR database
    Returns a list of companies matching the search term
    """
    base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
    
    params = {
        'company': company_name,
        'owner': 'exclude',
        'action': 'getcompany',
        'type': '10-K',
        'count': '10'
    }
    
    headers = {
        'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
    }
    
    try:
        logger.info(f"Searching SEC EDGAR for company: {company_name}")
        logger.info(f"Request URL: {base_url} with params: {params}")
        
        response = requests.get(base_url, params=params, headers=headers)
        
        # Log the response status
        logger.info(f"SEC EDGAR search response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"HTTP Error: {response.status_code} - {response.text}")
            return []
            
        response.raise_for_status()
        
        # Log response size to help with debugging
        logger.info(f"SEC EDGAR search response size: {len(response.text)} characters")
        
        # Save a snippet of the response for debugging
        response_snippet = response.text[:500] + "..." if len(response.text) > 500 else response.text
        logger.debug(f"Response snippet: {response_snippet}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if company was found
        no_results = soup.find(string=re.compile("No matching companies"))
        if no_results:
            logger.info(f"No matching companies found for: {company_name}")
            return []
        
        # If only one company matches, we might be redirected to the company page
        company_info = soup.find('span', {'class': 'companyName'})
        if company_info:
            logger.info(f"Found a single company match: {company_info.text if company_info else 'Unknown'}")
            cik = re.search(r'CIK=(\d+)', str(company_info))
            if cik:
                company_cik = cik.group(1)
                company_name = company_info.text.split('(')[0].strip()
                logger.info(f"Extracted CIK: {company_cik}, Company Name: {company_name}")
                return [{'cik': company_cik, 'name': company_name}]
            else:
                logger.warning(f"Could not extract CIK from company info: {str(company_info)}")
        
        # If multiple companies match, parse the results table
        companies = []
        results_table = soup.find('table', {'summary': 'Results'})
        if results_table:
            logger.info("Found results table with multiple companies")
            # Make sure results_table is a bs4 element before calling find_all
            rows = []
            if hasattr(results_table, 'find_all'):
                rows = results_table.find_all('tr')
                logger.info(f"Found {len(rows)-1} company rows in results table")
            else:
                logger.warning("Results table is not a proper BeautifulSoup element, cannot find rows")
            
            # Process rows only if we actually found some
            for row in rows[1:] if rows else []:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 2:
                    company_name = cols[1].text.strip()
                    cik_match = re.search(r'CIK=(\d+)', str(cols[0]))
                    if cik_match:
                        company_cik = cik_match.group(1)
                        companies.append({'cik': company_cik, 'name': company_name})
                        logger.info(f"Added company: {company_name} with CIK: {company_cik}")
                    else:
                        logger.warning(f"Could not extract CIK for company: {company_name} from column: {str(cols[0])}")
        else:
            logger.warning("Could not find results table in SEC EDGAR response")
        
        logger.info(f"Returning {len(companies)} companies from search results")
        return companies
        
    except Exception as e:
        logger.error(f"Error searching for company '{company_name}': {str(e)}")
        logger.exception("Exception details:")
        return []


def get_latest_10k(cik):
    """
    Get the latest 10-K filing for a company by CIK
    Returns the URL to the HTML version of the 10-K
    """
    # Format CIK with leading zeros
    cik_padded = cik.zfill(10)
    
    # First, get the list of all filings
    base_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    
    headers = {
        'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
    }
    
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        recent_filings = data.get('filings', {}).get('recent', {})
        
        # Find the most recent 10-K
        form_types = recent_filings.get('form', [])
        accession_numbers = recent_filings.get('accessionNumber', [])
        
        for i, form_type in enumerate(form_types):
            if form_type == '10-K' and i < len(accession_numbers):
                accession_number = accession_numbers[i].replace('-', '')
                
                # Build the URL to the HTML version of the 10-K
                html_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{accession_numbers[i]}-index.htm"
                
                # Get the actual document
                response = requests.get(html_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the link to the 10-K document (usually the one with "10-K" in the description)
                filing_links = soup.find_all('a')
                for link in filing_links:
                    if '10-K' in link.text and not 'XBRL' in link.text:
                        document_url = link.get('href')
                        if document_url:
                            # Convert relative URL to absolute URL
                            if document_url.startswith('/'):
                                document_url = f"https://www.sec.gov{document_url}"
                            elif not document_url.startswith('http'):
                                document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{document_url}"
                            
                            return document_url
                            
                # Try to find any HTM file that might be the 10-K
                for link in filing_links:
                    document_url = link.get('href')
                    if document_url and document_url.lower().endswith('.htm') and not 'index' in document_url.lower():
                        # Convert relative URL to absolute URL
                        if document_url.startswith('/'):
                            document_url = f"https://www.sec.gov{document_url}"
                        elif not document_url.startswith('http'):
                            document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{document_url}"
                        
                        return document_url
                
                # If we can't find a specific 10-K link, return the index page
                return html_url
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting 10-K for CIK {cik}: {str(e)}")
        return None


def extract_10k_content(url):
    """
    Extract content from a 10-K filing
    Returns the text content of the 10-K
    """
    headers = {
        'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
    }
    
    try:
        # First approach: Try direct extraction
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if we have an iXBRL document
        if 'ix?doc=' in url:
            logger.info(f"Detected iXBRL document, using specialized extraction for: {url}")
            
            # Try to get the main content element
            main_content = soup.find('div', {'class': 'filing-content'})
            if main_content:
                # Extract text from the main content element
                text = main_content.get_text(separator='\n', strip=True)
                if text and len(text) > 500:
                    return text
                    
            # If main content element not found or insufficient text, try the document body
            body = soup.find('body')
            if body:
                text = body.get_text(separator='\n', strip=True)
                if text and len(text) > 500:
                    return text
            
            # Second approach: Try to get the raw text version of the filing
            try:
                # Extract document details from URL
                if '/Archives/edgar/data/' in url:
                    parts = url.split('/ix?doc=/Archives/edgar/data/')[1].split('/')
                    if len(parts) >= 2:
                        cik = parts[0]
                        # Get the accession number
                        if len(parts) >= 3:
                            # Modern SEC URLs include the filename
                            accession_parts = parts[1].split('-')
                            accession = f"{accession_parts[0]}-{accession_parts[1]}-{accession_parts[2]}"
                            
                            # Try to request the text version
                            txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{parts[1]}/{accession}.txt"
                            logger.info(f"Attempting to retrieve text version: {txt_url}")
                            
                            txt_response = requests.get(txt_url, headers=headers)
                            txt_response.raise_for_status()
                            
                            if len(txt_response.text) > 1000:  # Ensure we got meaningful content
                                logger.info("Successfully retrieved text version of 10-K")
                                return txt_response.text
            except Exception as txt_err:
                logger.warning(f"Failed to get text version: {str(txt_err)}")
                
            # Third approach: Try alternative URL construction for modern SEC URLs
            try:
                # Sometimes we can access the HTM version directly
                if '/ix?doc=' in url:
                    htm_url = url.replace('/ix?doc=', '/')
                    logger.info(f"Attempting to retrieve HTM version: {htm_url}")
                    
                    htm_response = requests.get(htm_url, headers=headers)
                    htm_response.raise_for_status()
                    
                    htm_soup = BeautifulSoup(htm_response.text, 'html.parser')
                    htm_text = htm_soup.get_text(separator='\n', strip=True)
                    
                    if htm_text and len(htm_text) > 500:
                        logger.info("Successfully retrieved HTM version of 10-K")
                        return htm_text
            except Exception as htm_err:
                logger.warning(f"Failed to get HTM version: {str(htm_err)}")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Check if we have enough content
        if text and len(text) > 500:
            return text
        else:
            # Fallback to a more aggressive extraction approach
            logger.warning("Initial extraction produced insufficient content, trying fallback method")
            # Get all text nodes from the document
            text_nodes = []
            for node in soup.find_all(text=True):
                if node.parent.name not in ['script', 'style', 'meta', 'link']:
                    text_nodes.append(node.strip())
            
            # Filter out empty lines and join
            filtered_text = '\n'.join(node for node in text_nodes if node)
            
            if filtered_text and len(filtered_text) > 500:
                return filtered_text
            else:
                raise ValueError("Could not extract sufficient content from the 10-K filing")
        
    except Exception as e:
        logger.error(f"Error extracting content from 10-K at {url}: {str(e)}")
        raise ValueError(f"Failed to extract content from 10-K: {str(e)}")