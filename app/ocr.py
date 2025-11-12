import os
from pathlib import Path
from typing import Dict, List
import pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import logging

logger = logging.getLogger(__name__)


class OCRProcessor:
    def __init__(self):
        self.supported_formats = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}

    def process_document(self, file_path: str) -> Dict:
        """Process document and extract text"""
        file_ext = Path(file_path).suffix.lower()

        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")

        if file_ext == '.pdf':
            return self._process_pdf(file_path)
        else:
            return self._process_image(file_path)

    def _process_pdf(self, pdf_path: str) -> Dict:
        """Extract text from PDF using pdfplumber and OCR fallback"""
        pages_data = []

        try:
            # Try text extraction with pdfplumber first
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()

                    # If no text found, use OCR
                    if not text or len(text.strip()) < 50:
                        logger.info(f"Using OCR for page {page_num}")
                        text = self._ocr_pdf_page(pdf_path, page_num)

                    pages_data.append({
                        'page': page_num,
                        'text': text
                    })

            return {'pages': pages_data}

        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            # Fallback to full OCR
            return self._ocr_full_pdf(pdf_path)

    def _ocr_pdf_page(self, pdf_path: str, page_num: int) -> str:
        """OCR a specific PDF page"""
        try:
            images = convert_from_path(
                pdf_path,
                first_page=page_num,
                last_page=page_num,
                dpi=300
            )

            if images:
                return pytesseract.image_to_string(images[0])
            return ""
        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {e}")
            return ""

    def _ocr_full_pdf(self, pdf_path: str) -> Dict:
        """OCR entire PDF"""
        pages_data = []

        try:
            images = convert_from_path(pdf_path, dpi=300)

            for page_num, image in enumerate(images, 1):
                text = pytesseract.image_to_string(image)
                pages_data.append({
                    'page': page_num,
                    'text': text
                })

            return {'pages': pages_data}
        except Exception as e:
            logger.error(f"Full PDF OCR failed: {e}")
            return {'pages': []}

    def _process_image(self, image_path: str) -> Dict:
        """Extract text from image using OCR"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)

            return {
                'pages': [{
                    'page': 1,
                    'text': text
                }]
            }
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return {'pages': []}