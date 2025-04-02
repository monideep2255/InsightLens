import os
import logging
import tempfile
import time
import threading
import concurrent.futures
from functools import lru_cache
from tqdm import tqdm
import PyPDF2
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Page extraction statistics for monitoring processing time
page_processing_times = {}

def extract_pdf_content(pdf_path):
    """
    Extract text content from a PDF file using PyPDF2 for large files or LangChain for smaller files
    Returns a string containing the extracted text
    """
    try:
        start_time = time.time()
        
        # First, verify the PDF is valid
        num_pages = validate_pdf(pdf_path)
        
        # For very large PDFs (over 100 pages), use fast extraction with page sampling
        # This will sample important pages rather than process the entire document
        if num_pages > 100:
            logger.info(f"Large PDF detected ({num_pages} pages). Using optimized extraction.")
            content = extract_pdf_content_fast_parallel(pdf_path, num_pages)
        
        # For medium-sized PDFs (30-100 pages), use a hybrid approach for better performance
        elif num_pages > 30:
            logger.info(f"Medium-sized PDF detected ({num_pages} pages). Using semi-optimized extraction.")
            content = extract_pdf_content_medium_parallel(pdf_path, num_pages)
        
        # For smaller PDFs, use LangChain's PyPDFLoader
        else:
            logger.info(f"Small PDF detected ({num_pages} pages). Using comprehensive extraction.")
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Split into smaller chunks if needed - increase chunk size for better performance
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=3000,  # Larger chunks for better performance
                chunk_overlap=150  # Smaller overlap
            )
            
            # Get all chunks
            all_splits = text_splitter.split_documents(documents)
            
            # Combine all text
            content = ' '.join([doc.page_content for doc in all_splits])
        
        end_time = time.time()
        logger.info(f"PDF processing took {end_time - start_time:.2f} seconds for {num_pages} pages")
        
        return content
        
    except Exception as e:
        logger.error(f"Error extracting content from PDF {pdf_path}: {str(e)}")
        raise Exception(f"Failed to extract content from PDF: {str(e)}")


def extract_pdf_content_fast_parallel(pdf_path, total_pages):
    """
    Extract content from a large PDF by sampling key pages only
    Uses parallel processing for better performance
    """
    try:
        # Select pages to extract based on an improved sampling algorithm
        pages_to_extract = select_pages_to_extract(total_pages, 'fast')
        
        # Use parallel processing to extract text from pages
        return extract_pages_parallel(pdf_path, pages_to_extract, total_pages)
            
    except Exception as e:
        logger.error(f"Error extracting content from PDF {pdf_path}: {str(e)}")
        raise Exception(f"Failed to extract content from PDF: {str(e)}")

def extract_pdf_content_medium_parallel(pdf_path, total_pages):
    """
    Extract content from a medium-sized PDF by processing key pages and sampling others
    Uses parallel processing for better performance
    """
    try:
        # Select pages to extract based on an improved sampling algorithm
        pages_to_extract = select_pages_to_extract(total_pages, 'medium')
        
        # Use parallel processing to extract text from pages
        return extract_pages_parallel(pdf_path, pages_to_extract, total_pages)
            
    except Exception as e:
        logger.error(f"Error extracting content from PDF {pdf_path}: {str(e)}")
        raise Exception(f"Failed to extract content from PDF: {str(e)}")

def select_pages_to_extract(total_pages, mode='medium'):
    """
    Select pages to extract based on the document size and extraction mode
    
    Args:
        total_pages (int): Total number of pages in the document
        mode (str): 'fast', 'medium', or 'comprehensive'
        
    Returns:
        list: Pages to extract
    """
    pages_to_extract = []
    
    # Always include first pages (table of contents, intro)
    first_pages = 10 if mode != 'fast' else 5
    pages_to_extract.extend(range(min(first_pages, total_pages)))
    
    if mode == 'fast':
        # Executive summary (usually right after intro)
        if total_pages > 10:
            pages_to_extract.extend(range(5, min(10, total_pages)))
        
        # Business description (usually around 20-30% mark)
        if total_pages > 30:
            middle_start = int(total_pages * 0.2)
            pages_to_extract.extend(range(middle_start, middle_start + min(10, total_pages - middle_start)))
        
        # Financial section (usually around 40-60% mark)
        if total_pages > 50:
            financial_start = int(total_pages * 0.4)
            pages_to_extract.extend(range(financial_start, financial_start + min(15, total_pages - financial_start)))
            
            # Risk factors (usually around 25-35% mark)
            risk_start = int(total_pages * 0.3)
            pages_to_extract.extend(range(risk_start, risk_start + min(5, total_pages - risk_start)))
            
            # Management discussion (usually around 50-60% mark)
            md_start = int(total_pages * 0.55)
            pages_to_extract.extend(range(md_start, md_start + min(10, total_pages - md_start)))
        
        # If very large doc, sample every 20 pages throughout the middle
        if total_pages > 150:
            pages_to_extract.extend(range(30, total_pages - 20, 20))
        elif total_pages > 100:
            pages_to_extract.extend(range(30, total_pages - 20, 15))
        
    elif mode == 'medium':
        # For the middle section, take every nth page
        if total_pages > 20:
            middle_start = 10
            middle_end = total_pages - 5
            
            # Adjust sampling rate based on document size
            if total_pages > 80:
                step = 4
            elif total_pages > 50:
                step = 3
            else:
                step = 2
                
            pages_to_extract.extend(range(middle_start, middle_end, step))
    
    # Always include last pages (conclusions, signatures of executives)
    pages_to_extract.extend(range(max(0, total_pages - 5), total_pages))
    
    # Remove duplicates and sort
    return sorted(set(pages_to_extract))

def extract_pages_parallel(pdf_path, pages_to_extract, total_pages):
    """
    Extract text from pages using parallel processing
    
    Args:
        pdf_path (str): Path to the PDF file
        pages_to_extract (list): List of page numbers to extract
        total_pages (int): Total number of pages in the document
        
    Returns:
        str: Extracted text
    """
    # Open PDF file once and keep it open for all workers
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        
        # Determine the appropriate number of workers based on system and document size
        # For very large documents, use fewer workers to avoid memory issues
        if total_pages > 500:
            max_workers = min(4, os.cpu_count() or 4)
        else:
            max_workers = min(6, os.cpu_count() or 4)
        
        # Extract text using parallel processing
        content = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit extraction jobs for each page
            future_to_page = {
                executor.submit(extract_page_text, reader, i): i 
                for i in pages_to_extract if i < len(reader.pages)
            }
            
            # Process completed pages
            for future in concurrent.futures.as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    page_text = future.result()
                    if page_text:
                        content.append(f"[Page {page_num + 1}]\n{page_text}")
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {str(e)}")
        
        # Join all extracted text
        text = "\n\n".join(content)
        
        logger.info(f"Successfully extracted content from {len(pages_to_extract)} pages out of {total_pages}")
        return text

def extract_page_text(reader, page_num):
    """
    Extract text from a single page
    
    Args:
        reader (PdfReader): PyPDF2 reader object
        page_num (int): Page number to extract
        
    Returns:
        str: Extracted text
    """
    start_time = time.time()
    try:
        page = reader.pages[page_num]
        text = page.extract_text()
        
        # Track processing time for performance monitoring
        end_time = time.time()
        processing_time = end_time - start_time
        page_processing_times[page_num] = processing_time
        
        return text
    except Exception as e:
        logger.warning(f"Failed to extract text from page {page_num}: {str(e)}")
        return ""

@lru_cache(maxsize=16)
def validate_pdf(pdf_path):
    """
    Validate that the file is a readable PDF
    Returns the number of pages in the PDF
    Uses LRU cache to avoid repeatedly validating the same file
    """
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)
            if num_pages == 0:
                raise ValueError("PDF file has no pages")
            return num_pages
    except PyPDF2.errors.PdfReadError:
        raise ValueError("Invalid or corrupted PDF file")
    except Exception as e:
        raise ValueError(f"PDF validation error: {str(e)}")
