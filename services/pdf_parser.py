import os
import logging
import tempfile
import PyPDF2
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def extract_pdf_content(pdf_path):
    """
    Extract text content from a PDF file using LangChain's PDF Loader
    Returns a string containing the extracted text
    """
    try:
        # First, verify the PDF is valid
        validate_pdf(pdf_path)
        
        # Use LangChain's PyPDFLoader to extract content
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Split into smaller chunks if needed
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
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

def validate_pdf(pdf_path):
    """
    Validate that the file is a readable PDF
    """
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            if len(reader.pages) == 0:
                raise ValueError("PDF file has no pages")
    except PyPDF2.errors.PdfReadError:
        raise ValueError("Invalid or corrupted PDF file")
    except Exception as e:
        raise ValueError(f"PDF validation error: {str(e)}")
