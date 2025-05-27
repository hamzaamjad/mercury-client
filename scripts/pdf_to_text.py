#!/usr/bin/env python3
"""
Simple PDF to text converter script for extracting API documentation.
"""
import sys
import os
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Install with: pip install PyPDF2")
    sys.exit(1)

def pdf_to_text(pdf_path: str, output_path: str = None) -> str:
    """Convert PDF to text file."""
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return ""
    
    text_content = []
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_pages = len(pdf_reader.pages)
        
        print(f"Processing {num_pages} pages from {pdf_file.name}...")
        
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            text_content.append(f"\n--- Page {page_num + 1} ---\n")
            text_content.append(text)
    
    full_text = "\n".join(text_content)
    
    # Save to file if output path provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as out_file:
            out_file.write(full_text)
        print(f"Text saved to: {output_path}")
    
    return full_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_to_text.py <pdf_file> [output_file]")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not output_file:
        # Auto-generate output filename
        output_file = pdf_file.replace('.pdf', '.txt')
    
    pdf_to_text(pdf_file, output_file)