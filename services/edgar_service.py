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
        'count': '20'  # Request more results to increase chances of finding matches
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
            # Try to find CIK in the company_info
            cik_regex = re.compile(r'CIK=(\d+)', re.IGNORECASE)
            cik_match = cik_regex.search(str(company_info))
            if cik_match:
                company_cik = cik_match.group(1).lstrip('0')  # Remove leading zeros
                company_name = company_info.text.split('(')[0].strip()
                logger.info(f"Extracted CIK: {company_cik}, Company Name: {company_name}")
                return [{'cik': company_cik, 'name': company_name}]
            else:
                # If we can't extract CIK from company_info, try to find it elsewhere on the page
                cik_element = soup.find('input', {'name': 'CIK'}) or soup.find('span', string=re.compile(r'CIK.*\d+'))
                if cik_element:
                    cik_text = cik_element.get('value', '') if cik_element.get('value') else cik_element.text
                    cik_match = re.search(r'(\d+)', cik_text)
                    if cik_match:
                        company_cik = cik_match.group(1).lstrip('0')  # Remove leading zeros
                        company_name = company_info.text.split('(')[0].strip()
                        logger.info(f"Extracted CIK: {company_cik}, Company Name: {company_name}")
                        return [{'cik': company_cik, 'name': company_name}]
                
                logger.warning(f"Could not extract CIK from company info: {str(company_info)}")
        
        # If multiple companies match, parse the results table
        companies = []
        
        # Try to find results tables - there could be multiple formats
        results_tables = soup.find_all('table')
        
        # Try each table
        for results_table in results_tables:
            # Skip tables that are clearly not result tables
            if not hasattr(results_table, 'find_all'):
                continue
                
            # Try to extract rows
            rows = results_table.find_all('tr')
            if not rows or len(rows) <= 1:  # Skip if no data rows (header only)
                continue
                
            logger.info(f"Examining table with {len(rows)} rows")
            
            # Process rows
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue
                    
                # Extract company name from second column
                company_name_text = cols[1].text.strip()
                if not company_name_text:
                    continue
                    
                # Extract CIK from the row HTML
                row_html = str(row)
                cik_match = re.search(r'CIK=(\d+)', row_html) or re.search(r'cik=(\d+)', row_html)
                
                if cik_match:
                    company_cik = cik_match.group(1).lstrip('0')  # Remove leading zeros
                    companies.append({'cik': company_cik, 'name': company_name_text})
                    logger.info(f"Added company: {company_name_text} with CIK: {company_cik}")
                else:
                    # Check for CIK in the first column text
                    first_col_text = cols[0].text.strip()
                    cik_text_match = re.search(r'(\d{5,})', first_col_text)
                    
                    if cik_text_match:
                        company_cik = cik_text_match.group(1).lstrip('0')
                        companies.append({'cik': company_cik, 'name': company_name_text})
                        logger.info(f"Added company from text: {company_name_text} with CIK: {company_cik}")
                    else:
                        logger.warning(f"Could not extract CIK for company: {company_name_text}")
        
        # If we couldn't find any companies using tables, try looking for links with CIK
        if not companies:
            logger.info("Trying alternative company extraction method")
            # Look for links that might contain CIK information
            links = soup.find_all('a', href=re.compile(r'CIK=\d+', re.IGNORECASE))
            
            for link in links:
                href = link.get('href', '')
                cik_match = re.search(r'CIK=(\d+)', href, re.IGNORECASE)
                if cik_match and link.text and not 'index' in link.text.lower():
                    company_cik = cik_match.group(1).lstrip('0')  # Remove leading zeros
                    company_name_text = link.text.strip()
                    if company_name_text and not any(c['cik'] == company_cik for c in companies):
                        companies.append({'cik': company_cik, 'name': company_name_text})
                        logger.info(f"Added company from link: {company_name_text} with CIK: {company_cik}")
                        
        # If we still couldn't find any companies, use the Magnificent 7 as a fallback if the search term matches
        if not companies:
            magnificent_7 = [
                {"cik": "320193", "name": "Apple Inc."},
                {"cik": "789019", "name": "Microsoft Corporation"},
                {"cik": "1018724", "name": "Amazon.com, Inc."},
                {"cik": "1652044", "name": "Alphabet Inc. (Google)"},
                {"cik": "1326801", "name": "Meta Platforms, Inc. (Facebook)"},
                {"cik": "1318605", "name": "Tesla, Inc."},
                {"cik": "885639", "name": "NVIDIA Corporation"}
            ]
            
            # Check if the search term matches any of the Magnificent 7 company names
            search_term_lower = company_name.lower()
            for company in magnificent_7:
                if search_term_lower in company["name"].lower():
                    companies.append(company)
                    logger.info(f"Added matching Magnificent 7 company: {company['name']}")
        
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
        logger.info(f"Fetching submission data for CIK: {cik}")
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        recent_filings = data.get('filings', {}).get('recent', {})
        
        if not recent_filings:
            logger.warning(f"No recent filings found for CIK: {cik}")
            # Try alternative approach using the old search interface
            return get_latest_10k_alternative(cik)
        
        # Find the most recent 10-K
        form_types = recent_filings.get('form', [])
        accession_numbers = recent_filings.get('accessionNumber', [])
        filing_dates = recent_filings.get('filingDate', [])
        
        # Log what we found
        logger.info(f"Found {len(form_types)} recent filings for CIK: {cik}")
        
        # Create a list of filings with their dates for better selection
        filings = []
        for i, form_type in enumerate(form_types):
            if i < len(accession_numbers) and i < len(filing_dates):
                if form_type in ['10-K', '10-K/A']:  # Include amended 10-Ks as well
                    filings.append({
                        'form_type': form_type,
                        'accession_number': accession_numbers[i],
                        'filing_date': filing_dates[i]
                    })
        
        # Sort by filing date, most recent first
        filings.sort(key=lambda x: x['filing_date'], reverse=True)
        
        # Log what 10-K filings we found
        logger.info(f"Found {len(filings)} 10-K/10-K/A filings for CIK: {cik}")
        for filing in filings:
            logger.info(f"  {filing['form_type']} - {filing['filing_date']}")
        
        # Process each 10-K, starting with the most recent
        for filing in filings:
            try:
                accession_number = filing['accession_number'].replace('-', '')
                
                # Build the URL to the HTML version of the 10-K
                index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{filing['accession_number']}-index.htm"
                logger.info(f"Checking index page: {index_url}")
                
                # Get the filing index page
                response = requests.get(index_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find the document table that contains the actual filings
                filing_tables = soup.find_all('table')
                
                document_found = False
                for table in filing_tables:
                    # Look for links in the table
                    links = table.find_all('a')
                    
                    # First priority: Find the link with "10-K" or specific formats in the text
                    for link in links:
                        link_text = link.text.strip().upper()
                        if (('10-K' in link_text and 'XBRL' not in link_text) or 
                            (('10K' in link_text or '10-K' in link_text) and not any(x in link_text for x in ['XBRL', 'ZIP', 'GRAPHIC']))):
                            document_url = link.get('href')
                            if document_url:
                                # Convert relative URL to absolute URL
                                if document_url.startswith('/'):
                                    document_url = f"https://www.sec.gov{document_url}"
                                elif not document_url.startswith('http'):
                                    document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{document_url}"
                                
                                logger.info(f"Found 10-K document link: {document_url}")
                                return document_url
                    
                    # Second priority: Find any HTM file that might be the 10-K, excluding specific patterns
                    if not document_found:
                        for link in links:
                            href = link.get('href', '')
                            
                            # Skip certain file types or patterns
                            if (href and 
                                href.lower().endswith('.htm') and 
                                not any(x in href.lower() for x in ['index', 'xbrl', 'xml', 'def', 'lab', 'pre']) and
                                not any(x in link.text.lower() for x in ['graphic', 'image', 'jpg', 'png'])):
                                # Convert relative URL to absolute URL
                                if href.startswith('/'):
                                    document_url = f"https://www.sec.gov{href}"
                                elif not href.startswith('http'):
                                    document_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{href}"
                                else:
                                    document_url = href
                                
                                logger.info(f"Found potential 10-K HTM document: {document_url}")
                                document_found = True
                                return document_url
                
                # If we get here and haven't found a direct document link, try modern SEC viewer format
                viewer_url = f"https://www.sec.gov/ix?doc=/Archives/edgar/data/{cik}/{accession_number}/{filing['accession_number']}.htm"
                logger.info(f"Trying modern SEC viewer format: {viewer_url}")
                
                try:
                    # Check if the modern viewer URL works
                    viewer_response = requests.get(viewer_url, headers=headers)
                    if viewer_response.status_code == 200:
                        logger.info(f"Modern SEC viewer format works: {viewer_url}")
                        return viewer_url
                except Exception as viewer_err:
                    logger.warning(f"Failed to access modern SEC viewer: {str(viewer_err)}")
                
                # If no specific document found, use the index page as a last resort
                logger.info(f"No specific document found, returning index page: {index_url}")
                return index_url
                
            except Exception as filing_err:
                logger.warning(f"Error processing filing {filing['accession_number']}: {str(filing_err)}")
                continue
        
        # Try alternative approach if the modern API didn't work
        logger.warning("Modern API approach failed, trying alternative method")
        return get_latest_10k_alternative(cik)
        
    except Exception as e:
        logger.error(f"Error getting 10-K for CIK {cik}: {str(e)}")
        # Try alternative approach as a fallback
        return get_latest_10k_alternative(cik)


def get_latest_10k_alternative(cik):
    """
    Alternative method to get the latest 10-K filing using the browse-edgar interface
    Used as a fallback if the submissions API method fails
    """
    base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
    
    params = {
        'CIK': cik,
        'owner': 'exclude',
        'action': 'getcompany',
        'type': '10-K',
        'count': '5'  # Get the 5 most recent 10-Ks
    }
    
    headers = {
        'User-Agent': 'InsightLens Research Tool (contactus@example.com)'
    }
    
    try:
        logger.info(f"Using alternative method to fetch 10-K for CIK: {cik}")
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all document links in the table
        doc_links = []
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'Archives' in href and '/index.html' in href:
                doc_links.append(f"https://www.sec.gov{href}")
        
        # If we found document links, process the first (most recent) one
        if doc_links:
            logger.info(f"Found {len(doc_links)} document links in alternative search")
            # Get the first (most recent) document index page
            index_url = doc_links[0]
            logger.info(f"Processing index page: {index_url}")
            
            # Get the document index page
            response = requests.get(index_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find the actual 10-K document
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href and '.htm' in href.lower() and not '/index' in href.lower():
                    # Some URLs are already absolute, others are relative
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        return f"https://www.sec.gov{href}"
                    else:
                        # Construct full URL using the index page as base
                        base_parts = index_url.split('/')
                        base_parts.pop()  # Remove 'index.html'
                        base_url = '/'.join(base_parts)
                        return f"{base_url}/{href}"
            
            # If we couldn't find a specific document, return the index page
            return index_url
            
        # If we couldn't find any document links, look for archived documents
        archived_link = None
        for link in soup.find_all('a'):
            if 'Archives' in link.get('href', '') and '10-K' in link.text:
                archived_link = f"https://www.sec.gov{link.get('href')}"
                break
        
        if archived_link:
            logger.info(f"Found archived 10-K link: {archived_link}")
            return archived_link
        
        logger.warning(f"No 10-K found for CIK {cik} using alternative method")
        return None
        
    except Exception as e:
        logger.error(f"Error in alternative method for CIK {cik}: {str(e)}")
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