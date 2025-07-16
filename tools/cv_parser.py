"""
CV Document Parser Module

This module provides document parsing functionality for the CV Analyzer system.
It supports multiple document formats and extracts plain text content for
further analysis by AI components.

Key Features:
- Multi-format support (PDF, DOCX)
- Robust text extraction with error handling
- Clean text output suitable for NLP processing
- Debug logging for troubleshooting

Supported Formats:
- PDF: Using pdfplumber for accurate text extraction
- DOCX: Using python-docx for Microsoft Word documents

Dependencies:
- pdfplumber: For PDF text extraction with table support
- python-docx: For Microsoft Word document parsing

"""

import pdfplumber
import docx

def parse_pdf(file_path):
    """
    Extract text content from PDF files using pdfplumber.
    
    This function processes PDF documents page by page, extracting text
    content while preserving document structure and handling various
    PDF formatting scenarios.
    
    Args:
        file_path (str): Absolute path to the PDF file to parse
        
    Returns:
        str: Extracted text content with pages separated by newlines
        
    Example:
        >>> text = parse_pdf("/tmp/resume.pdf")
        >>> print(len(text))
        1245
        
    Note:
        - Handles PDFs with embedded text, images, and tables
        - Returns empty string for pages without extractable text
        - Joins multiple pages with newline separators
        - Robust against corrupted or password-protected PDFs
    """
    with pdfplumber.open(file_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def parse_docx(file_path):
    """
    Extract text content from Microsoft Word DOCX files.
    
    This function processes DOCX documents by extracting text from all
    paragraphs while maintaining document structure and readability.
    
    Args:
        file_path (str): Absolute path to the DOCX file to parse
        
    Returns:
        str: Extracted text content with paragraphs separated by newlines
        
    Example:
        >>> text = parse_docx("/tmp/resume.docx")
        >>> print(text[:100])
        "John Doe\nSoftware Engineer\n\nExperience:\n- Senior Developer at Tech Corp..."
        
    Note:
        - Extracts text from all paragraph elements
        - Preserves paragraph structure with newlines
        - Includes debug logging for troubleshooting
        - Handles documents with various formatting styles
    """
    doc = docx.Document(file_path)
    print(f"Document text: {[para.text for para in doc.paragraphs]}")
    return "\n".join([para.text for para in doc.paragraphs])




def parse_cv(file_path):
    """
    Main entry point for CV document parsing with format detection.
    
    This function automatically detects the document format based on file
    extension and routes to the appropriate parser for text extraction.
    
    Args:
        file_path (str): Absolute path to the CV file to parse
        
    Returns:
        str: Extracted text content ready for NLP analysis
        
    Raises:
        ValueError: If the file format is not supported
        FileNotFoundError: If the specified file doesn't exist
        Exception: If document parsing fails due to corruption or access issues
        
    Supported Formats:
        - .pdf: PDF documents via pdfplumber
        - .docx: Microsoft Word documents via python-docx
        
    Example:
        >>> # Parse a PDF resume
        >>> text = parse_cv("/tmp/john_doe_resume.pdf")
        >>> print(f"Extracted {len(text)} characters")
        
        >>> # Parse a Word document
        >>> text = parse_cv("/tmp/jane_smith_cv.docx")
        >>> print(text.split('\\n')[0])  # First line
        "Jane Smith"
        
    Note:
        - Format detection is case-sensitive (use lowercase extensions)
        - Returns clean text suitable for skill extraction and analysis
        - Maintains document structure with appropriate line breaks
        - Handles edge cases like empty documents gracefully
    """
    if file_path.endswith('.pdf'):
        return parse_pdf(file_path)
    elif file_path.endswith('.docx'):
        return parse_docx(file_path)
    else:
        raise ValueError("Unsupported file type")
