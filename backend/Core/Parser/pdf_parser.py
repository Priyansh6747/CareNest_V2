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


def detect_sections(text: str) -> Dict[str, str]:
    """
    Detect and extract common medical report sections.
    
    Returns:
        Dictionary with section names as keys and content as values
    """
    # Common section headers in medical reports
    section_patterns = [
        # Vital signs
        (r'(?:^|\n)\s*(VITALS?|VITAL\s*SIGNS?)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'vitals'),
        # Medications
        (r'(?:^|\n)\s*(MEDICATIONS?|CURRENT\s*MEDICATIONS?|MEDS?)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'medications'),
        # Lab results
        (r'(?:^|\n)\s*(LAB(?:ORATORY)?\s*(?:RESULTS?|VALUES?)?|LABS?)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'lab_results'),
        # Physical exam
        (r'(?:^|\n)\s*(PHYSICAL\s*EXAM(?:INATION)?|PE)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'physical_exam'),
        # Chief complaint
        (r'(?:^|\n)\s*(CHIEF\s*COMPLAINT|CC)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'chief_complaint'),
        # History
        (r'(?:^|\n)\s*(HISTORY\s*OF\s*PRESENT\s*ILLNESS|HPI)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'history'),
        # Impression/Assessment
        (r'(?:^|\n)\s*(IMPRESSION|ASSESSMENT|DIAGNOSIS|DX)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'impression'),
        # Plan
        (r'(?:^|\n)\s*(PLAN|TREATMENT\s*PLAN|RECOMMENDATIONS?)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'plan'),
        # Obstetric/Maternal
        (r'(?:^|\n)\s*(OBSTETRIC\s*HISTORY|OB\s*HISTORY|PREGNANCY\s*HISTORY)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'obstetric_history'),
        # Gestational info
        (r'(?:^|\n)\s*(GESTATIONAL\s*AGE|GA|EDD|DUE\s*DATE)\s*:?\s*\n?([\s\S]*?)(?=\n\s*[A-Z]{2,}|$)', 'gestational_info'),
    ]
    
    sections = {}
    
    for pattern, section_name in section_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            content = match.group(2).strip() if len(match.groups()) > 1 else match.group(1).strip()
            sections[section_name] = content
    
    return sections


def extract_structured_data(pdf_path: str) -> Dict:
    """
    Extract structured data from PDF including text, tables, and sections.
    
    Returns:
        Dictionary with text, tables, and detected sections
    """
    text = extract_text_from_pdf(pdf_path)
    tables = extract_tables_from_pdf(pdf_path)
    sections = detect_sections(text)
    
    return {
        "full_text": text,
        "tables": tables,
        "sections": sections,
        "has_sections": len(sections) > 0
    }