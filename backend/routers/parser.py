"""
Parser router - endpoints for PDF parsing and text extraction
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, status
import tempfile
import os

from Core.Parser.pdf_parser import (
    extract_text_from_pdf,
    extract_tables_from_pdf,
)

router = APIRouter(prefix="/parser", tags=["Parser"])


# ============================================================================
# PDF Text Extraction Endpoints
# ============================================================================

@router.post(
    "/pdf/extract-text",
    summary="Extract text from PDF",
    description="Upload a PDF file and extract all text content using the specified method.",
)
async def extract_pdf_text(
    file: UploadFile = File(..., description="PDF file to extract text from"),
    method: str = Query(default="pdfplumber", regex="^(pdfplumber|pymupdf)$", description="Extraction method to use")
):
    """
    Extract text from an uploaded PDF file.
    
    Args:
        file: The PDF file to process
        method: Extraction method - either 'pdfplumber' or 'pymupdf'
    
    Returns:
        Dictionary containing extracted text and metadata
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Create temporary file to store uploaded PDF
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Extract text using specified method
        extracted_text = extract_text_from_pdf(temp_path, method=method)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return {
            "filename": file.filename,
            "method": method,
            "text": extracted_text,
            "text_length": len(extracted_text),
            "success": True
        }
        
    except Exception as e:
        # Clean up temporary file in case of error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


@router.post(
    "/pdf/extract-tables",
    summary="Extract tables from PDF",
    description="Upload a PDF file and extract all tables (useful for lab results, structured data).",
)
async def extract_pdf_tables(
    file: UploadFile = File(..., description="PDF file to extract tables from")
):
    """
    Extract tables from an uploaded PDF file.
    
    Args:
        file: The PDF file to process
    
    Returns:
        Dictionary containing extracted tables with page numbers and data
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Create temporary file to store uploaded PDF
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Extract tables
        tables = extract_tables_from_pdf(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return {
            "filename": file.filename,
            "tables": tables,
            "table_count": len(tables),
            "success": True
        }
        
    except Exception as e:
        # Clean up temporary file in case of error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract tables from PDF: {str(e)}"
        )


@router.post(
    "/pdf/extract-all",
    summary="Extract both text and tables from PDF",
    description="Upload a PDF file and extract all content including text and tables.",
)
async def extract_pdf_all(
    file: UploadFile = File(..., description="PDF file to extract content from"),
    text_method: str = Query(default="pdfplumber", regex="^(pdfplumber|pymupdf)$", description="Text extraction method")
):
    """
    Extract both text and tables from an uploaded PDF file.
    
    Args:
        file: The PDF file to process
        text_method: Text extraction method - either 'pdfplumber' or 'pymupdf'
    
    Returns:
        Dictionary containing both extracted text and tables with metadata
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Create temporary file to store uploaded PDF
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Extract text
        extracted_text = extract_text_from_pdf(temp_path, method=text_method)
        
        # Extract tables
        tables = extract_tables_from_pdf(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return {
            "filename": file.filename,
            "text": {
                "content": extracted_text,
                "length": len(extracted_text),
                "method": text_method
            },
            "tables": {
                "data": tables,
                "count": len(tables)
            },
            "success": True
        }
        
    except Exception as e:
        # Clean up temporary file in case of error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract content from PDF: {str(e)}"
        )
