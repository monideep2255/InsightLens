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
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if company was found
        no_results = soup.find(string=re.compile("No matching companies"))
        if no_results:
            return []
        
        # If only one company matches, we might be redirected to the company page
        company_info = soup.find('span', {'class': 'companyName'})
        if company_info:
            cik = re.search(r'CIK=(\d+)', str(company_info))
            if cik:
                company_cik = cik.group(1)
                company_name = company_info.text.split('(')[0].strip()
                return [{'cik': company_cik, 'name': company_name}]
        
        # If multiple companies match, parse the results table
        companies = []
        results_table = soup.find('table', {'summary': 'Results'})
        if results_table:
            rows = results_table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 2:
                    company_name = cols[1].text.strip()
                    cik_match = re.search(r'CIK=(\d+)', str(cols[0]))
                    if cik_match:
                        company_cik = cik_match.group(1)
                        companies.append({'cik': company_cik, 'name': company_name})
        
        return companies
        
    except Exception as e:
        logger.error(f"Error searching for company: {str(e)}")
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
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        logger.error(f"Error extracting content from 10-K at {url}: {str(e)}")
        return None