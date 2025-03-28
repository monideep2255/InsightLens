import os
import logging
import tempfile
import PyPDF2
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def extract_pdf_content(pdf_path):
    """
    Extract text content from a PDF file using PyPDF2 for large files or LangChain for smaller files
    Returns a string containing the extracted text
    """
    try:
        # First, verify the PDF is valid
        num_pages = validate_pdf(pdf_path)
        
        # For very large PDFs (over 100 pages), use fast extraction with page sampling
        # This will sample important pages rather than process the entire document
        if num_pages > 100:
            logger.info(f"Large PDF detected ({num_pages} pages). Using optimized extraction.")
            return extract_pdf_content_fast(pdf_path, num_pages)
        
        # For medium-sized PDFs (30-100 pages), use a hybrid approach for better performance
        elif num_pages > 30:
            logger.info(f"Medium-sized PDF detected ({num_pages} pages). Using semi-optimized extraction.")
            return extract_pdf_content_medium(pdf_path, num_pages)
        
        # For smaller PDFs, use LangChain's PyPDFLoader
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
        full_content = ' '.join([doc.page_content for doc in all_splits])
        
        logger.info(f"Successfully extracted content from PDF: {pdf_path}")
        return full_content
        
    except Exception as e:
        logger.error(f"Error extracting content from PDF {pdf_path}: {str(e)}")
        raise Exception(f"Failed to extract content from PDF: {str(e)}")


def extract_pdf_content_fast(pdf_path, total_pages):
    """
    Extract content from a large PDF by sampling key pages only
    This is much faster than processing the entire document
    """
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            # Define which pages to extract based on document size
            pages_to_extract = []
            
            # Always include first 5 pages (table of contents, intro)
            pages_to_extract.extend(range(min(5, total_pages)))
            
            # Add some pages from the beginning (executive summary)
            if total_pages > 10:
                pages_to_extract.extend(range(5, min(10, total_pages)))
            
            # Add some pages from the middle sections (business description, usually around 20-30% mark)
            if total_pages > 30:
                middle_start = int(total_pages * 0.2)
                pages_to_extract.extend(range(middle_start, middle_start + min(10, total_pages - middle_start)))
            
            # Add some pages from financial section (usually around 40-60% mark)
            if total_pages > 50:
                financial_start = int(total_pages * 0.4)
                pages_to_extract.extend(range(financial_start, financial_start + min(15, total_pages - financial_start)))
            
            # If very large doc, sample every 20 pages throughout the middle
            if total_pages > 100:
                pages_to_extract.extend(range(30, total_pages - 20, 20))
            
            # Always include last few pages (conclusions, signatures of executives)
            if total_pages > 10:
                pages_to_extract.extend(range(max(0, total_pages - 5), total_pages))
            
            # Remove duplicates and sort
            pages_to_extract = sorted(set(pages_to_extract))
            
            # Extract text from selected pages
            content = []
            for i in pages_to_extract:
                if i < len(reader.pages):
                    page = reader.pages[i]
                    content.append(page.extract_text())
            
            # Join all extracted text
            text = "\n\n".join(content)
            
            logger.info(f"Successfully extracted content from {len(pages_to_extract)} pages out of {total_pages}")
            return text
            
    except Exception as e:
        logger.error(f"Error extracting content from PDF {pdf_path}: {str(e)}")
        raise Exception(f"Failed to extract content from PDF: {str(e)}")

def extract_pdf_content_medium(pdf_path, total_pages):
    """
    Extract content from a medium-sized PDF by processing key pages and sampling others
    This is a balance between comprehensive extraction and performance
    """
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            # Define which pages to extract based on document size
            pages_to_extract = []
            
            # Always include first 10 pages (table of contents, intro)
            pages_to_extract.extend(range(min(10, total_pages)))
            
            # For the middle section, take every 3rd page
            if total_pages > 20:
                middle_start = 10
                middle_end = total_pages - 5
                pages_to_extract.extend(range(middle_start, middle_end, 3))
            
            # Always include last 5 pages
            pages_to_extract.extend(range(max(0, total_pages - 5), total_pages))
            
            # Remove duplicates and sort
            pages_to_extract = sorted(set(pages_to_extract))
            
            # Extract text from selected pages
            content = []
            for i in pages_to_extract:
                if i < len(reader.pages):
                    page = reader.pages[i]
                    content.append(page.extract_text())
            
            # Join all extracted text
            text = "\n\n".join(content)
            
            logger.info(f"Successfully extracted content from {len(pages_to_extract)} pages out of {total_pages}")
            return text
            
    except Exception as e:
        logger.error(f"Error extracting content from PDF {pdf_path}: {str(e)}")
        raise Exception(f"Failed to extract content from PDF: {str(e)}")

def validate_pdf(pdf_path):
    """
    Validate that the file is a readable PDF
    Returns the number of pages in the PDF
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
