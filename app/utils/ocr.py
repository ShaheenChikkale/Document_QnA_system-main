"""
OCR Utilities for Scanned Documents
Handles text extraction from images and scanned PDFs
"""
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import tempfile
from typing import Optional, List
from langdetect import detect, LangDetectException


class OCRProcessor:
    """OCR processing for scanned documents"""
    
    def __init__(self):
        """Initialize OCR processor"""
        self.supported_languages = ['eng', 'spa', 'fra', 'deu', 'ita', 'por', 'hin', 'ara', 'chi_sim', 'jpn']
    
    def extract_text_from_image(
        self,
        image_path: str,
        lang: str = 'eng'
    ) -> str:
        """
        Extract text from an image file using OCR
        
        Args:
            image_path: Path to image file
            lang: Tesseract language code
            
        Returns:
            Extracted text
        """
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=lang)
            return text.strip()
        except Exception as e:
            raise ValueError(f"OCR failed for image: {str(e)}")
    
    def extract_text_from_pdf_with_ocr(
        self,
        pdf_path: str,
        lang: str = 'eng'
    ) -> str:
        """
        Extract text from a scanned PDF using OCR
        
        Args:
            pdf_path: Path to PDF file
            lang: Tesseract language code
            
        Returns:
            Extracted text from all pages
        """
        try:
            # Convert PDF pages to images
            images = convert_from_path(pdf_path)
            
            extracted_texts = []
            for i, image in enumerate(images):
                # Save temporary image
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    image.save(tmp.name, 'PNG')
                    tmp_path = tmp.name
                
                # Extract text from image
                text = pytesseract.image_to_string(image, lang=lang)
                extracted_texts.append(f"--- Page {i + 1} ---\n{text}")
                
                # Clean up temporary file
                os.unlink(tmp_path)
            
            return "\n\n".join(extracted_texts)
        except Exception as e:
            raise ValueError(f"OCR failed for PDF: {str(e)}")
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Tesseract language code
        """
        if not text or len(text.strip()) < 10:
            return 'eng'
        
        try:
            lang_code = detect(text)
            # Map to Tesseract language codes
            lang_map = {
                'en': 'eng',
                'es': 'spa',
                'fr': 'fra',
                'de': 'deu',
                'it': 'ita',
                'pt': 'por',
                'hi': 'hin',
                'ar': 'ara',
                'zh-cn': 'chi_sim',
                'ja': 'jpn'
            }
            return lang_map.get(lang_code, 'eng')
        except LangDetectException:
            return 'eng'
    
    def is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        Check if PDF is likely scanned (no extractable text)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if likely scanned
        """
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            
            # Check first few pages for text
            pages_to_check = min(3, len(reader.pages))
            total_text_length = 0
            
            for i in range(pages_to_check):
                text = reader.pages[i].extract_text()
                total_text_length += len(text.strip())
            
            # If very little text found, likely scanned
            return total_text_length < 100
        except Exception:
            return True  # Assume scanned if can't determine


def create_ocr_processor() -> OCRProcessor:
    """Factory function to create OCR processor"""
    return OCRProcessor()
