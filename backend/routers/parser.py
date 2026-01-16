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


# ============================================================================
# NER & Insights Endpoints
# ============================================================================

from pydantic import BaseModel
from Core.Parser.ner_processor import MedicalNERExtractor
from Core.Parser.insights_generator import generate_clinical_insights

# Global NER extractor (lazy loaded)
_ner_extractor = None

def get_ner_extractor():
    global _ner_extractor
    if _ner_extractor is None:
        _ner_extractor = MedicalNERExtractor()
    return _ner_extractor


class TextInput(BaseModel):
    text: str
    confidence_threshold: float = 0.7
    entity_types: Optional[List[str]] = None


class EntitiesResponse(BaseModel):
    entities: List[Dict]
    highlighted_text: str
    entity_count: int
    success: bool


@router.post(
    "/extract-entities",
    summary="Extract medical entities from text",
    description="Use NER to extract medications, conditions, measurements, etc. from medical text.",
    response_model=EntitiesResponse
)
async def extract_entities(input_data: TextInput):
    """
    Extract medical entities from text using scispaCy NER.
    
    Returns:
        Extracted entities with types, positions, and confidence scores
    """
    try:
        extractor = get_ner_extractor()
        entities_df, highlighted_text = extractor.extract_entities(
            input_data.text,
            confidence_threshold=input_data.confidence_threshold,
            entity_types=input_data.entity_types
        )
        
        entities = entities_df.to_dict('records') if not entities_df.empty else []
        
        return EntitiesResponse(
            entities=entities,
            highlighted_text=highlighted_text,
            entity_count=len(entities),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract entities: {str(e)}"
        )


class InsightsInput(BaseModel):
    text: str
    entities: Optional[List[Dict]] = None


@router.post(
    "/insights",
    summary="Generate clinical insights",
    description="Generate clinical insights from medical text or pre-extracted entities.",
)
async def generate_insights(input_data: InsightsInput):
    """
    Generate clinical insights from medical text.
    
    If entities are not provided, they will be extracted first.
    """
    import pandas as pd
    
    try:
        # If entities not provided, extract them first
        if input_data.entities is None:
            extractor = get_ner_extractor()
            entities_df, _ = extractor.extract_entities(input_data.text)
        else:
            entities_df = pd.DataFrame(input_data.entities)
        
        # Generate insights
        insights = generate_clinical_insights(entities_df, input_data.text)
        
        return {
            "insights": insights,
            "entity_count": len(entities_df) if not entities_df.empty else 0,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.post(
    "/analyze",
    summary="Full analysis pipeline",
    description="Complete analysis: extract text (if PDF), extract entities, generate insights.",
)
async def analyze_report(
    text: Optional[str] = None,
    file: Optional[UploadFile] = File(None),
):
    """
    Full analysis pipeline for medical reports.
    
    Accepts either raw text or a PDF file.
    """
    import pandas as pd
    
    try:
        # Get text from input
        if file is not None:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only PDF files are supported"
                )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            report_text = extract_text_from_pdf(temp_path)
            os.unlink(temp_path)
            
        elif text is not None:
            report_text = text
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'text' or 'file' must be provided"
            )
        
        # Extract entities
        extractor = get_ner_extractor()
        entities_df, highlighted_text = extractor.extract_entities(report_text)
        entities = entities_df.to_dict('records') if not entities_df.empty else []
        
        # Generate insights
        insights = generate_clinical_insights(entities_df, report_text)
        
        return {
            "text": report_text,
            "text_length": len(report_text),
            "entities": entities,
            "entity_count": len(entities),
            "insights": insights,
            "highlighted_text": highlighted_text,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze report: {str(e)}"
        )
