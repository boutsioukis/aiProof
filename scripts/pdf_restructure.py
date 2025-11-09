#!/usr/bin/env python3

import os
import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from pypdf import PdfReader, PdfWriter

project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

def get_chapter_boundaries(pdf_path: Path, api_key: str):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    print("Uploading PDF to Gemini...")
    file = genai.upload_file(path=str(pdf_path))
    
    print("Analyzing PDF structure...")
    prompt = """Analyze this PDF book and identify the exact page numbers where each chapter starts and ends, including all exercises for each chapter.

Return ONLY a valid JSON object with this exact format:
{
  "chapters": [
    {"chapter_number": 1, "chapter_title": "Chapter Title", "start_page": 5, "end_page": 45},
    {"chapter_number": 2, "chapter_title": "Chapter Title", "start_page": 46, "end_page": 89},
    ...
  ]
}

Page numbers should be 1-indexed (first page is page 1). Ensure end_page includes all exercises for that chapter. Return ONLY the JSON, no other text."""
    
    response = model.generate_content([file, prompt])
    response_text = response.text.strip()
    
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()
    
    result = json.loads(response_text)
    genai.delete_file(file.name)
    
    return result.get("chapters", [])

def split_pdf(pdf_path: Path, chapters: list, output_dir: Path):
    reader = PdfReader(pdf_path)
    
    print(f"\nSplitting PDF into {len(chapters)} chapters...")
    
    for chapter in chapters:
        start_page = chapter["start_page"] - 1
        end_page = chapter["end_page"]
        
        writer = PdfWriter()
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        safe_title = "".join(c for c in chapter["chapter_title"] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        
        output_filename = f"Chapter_{chapter['chapter_number']:02d}_{safe_title}.pdf"
        output_path = output_dir / output_filename
        
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        print(f"  Created: {output_filename} (pages {chapter['start_page']}-{chapter['end_page']})")

def main():
    parser = argparse.ArgumentParser(description='Split PDF by chapters using Gemini')
    parser.add_argument('pdf_file', type=str, help='Path to PDF file')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory')
    parser.add_argument('--api-key', type=str, default=None, help='Gemini API key')
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY required")
        sys.exit(1)
    
    output_dir = Path(args.output_dir) if args.output_dir else pdf_path.parent / f"{pdf_path.stem}_chapters"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        chapters = get_chapter_boundaries(pdf_path, api_key)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    if not chapters:
        print("Error: No chapters identified")
        sys.exit(1)
    
    print(f"\nFound {len(chapters)} chapters:")
    for ch in chapters:
        print(f"  Chapter {ch['chapter_number']}: {ch['chapter_title']} (pages {ch['start_page']}-{ch['end_page']})")
    
    try:
        split_pdf(pdf_path, chapters, output_dir)
        print(f"\n✓ Successfully split PDF into {len(chapters)} chapters")
        print(f"  Output directory: {output_dir}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

