import os
import json
import uuid
from pathlib import Path
from typing import Dict, List
from fastapi import UploadFile
import aiofiles

from app.config import settings
from app.ocr import OCRProcessor
from app.utils import chunk_text


class DocumentIngestion:
    def __init__(self):
        self.ocr = OCRProcessor()
        self.metadata_file = os.path.join(settings.PROCESSED_DIR, "documents.json")
        self._load_metadata()

    def _load_metadata(self):
        """Load document metadata from disk"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                self.documents = json.load(f)
        else:
            self.documents = {}

    def _save_metadata(self):
        """Save document metadata to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.documents, f, indent=2)

    async def process_upload(self, file: UploadFile) -> Dict:
        """Process uploaded file"""
        # Generate unique document ID
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Save uploaded file
        file_ext = Path(file.filename).suffix.lower()
        saved_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}{file_ext}")

        async with aiofiles.open(saved_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Process document (OCR + chunking)
        text_content = self.ocr.process_document(saved_path)

        # Chunk text
        chunks = chunk_text(text_content, chunk_size=512, overlap=50)

        # Store metadata
        doc_metadata = {
            'doc_id': doc_id,
            'filename': file.filename,
            'file_path': saved_path,
            'pages': len(text_content.get('pages', [])),
            'chunks': chunks
        }

        self.documents[doc_id] = doc_metadata
        self._save_metadata()

        return doc_metadata

    def get_all_documents(self) -> List[Dict]:
        """Get all processed documents"""
        return list(self.documents.values())

    def get_document(self, doc_id: str) -> Dict:
        """Get specific document metadata"""
        return self.documents.get(doc_id)