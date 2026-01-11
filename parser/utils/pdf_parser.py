import pdfplumber
import fitz  # PyMuPDF
from typing import Optional, List, Dict
import re

def extract_text_from_pdf(pdf_path: str, method: str = "pdfplumber") -> str:
    """
    Extract text from PDF using specified method
    
    Args:
        pdf_path: Path to PDF file
        method: "pdfplumber" or "pymupdf"
    
    Returns:
        Extracted text as string
    """
    text = ""
    
    try:
        if method == "pdfplumber":
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        
        elif method == "pymupdf":
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        
        # Clean up text
        text = clean_extracted_text(text)
        
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    return text

def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers and headers/footers
    text = re.sub(r'\n\d+\n', '\n', text)
    
    # Fix common OCR issues
    replacements = {
        'ﬁ': 'fi',
        'ﬂ': 'fl',
        'ﬀ': 'ff',
        'ﬃ': 'ffi',
        'ﬄ': 'ffl',
        '•': '-',
        '�': ''
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text.strip()

def extract_tables_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract tables from PDF (for lab results, etc.)
    """
    tables = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for table_num, table in enumerate(page_tables):
                    if table:
                        tables.append({
                            "page": page_num + 1,
                            "table_num": table_num + 1,
                            "data": table
                        })
    except Exception as e:
        print(f"Warning: Could not extract tables: {e}")
    
    return tables