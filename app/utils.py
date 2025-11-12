import logging
import os
from typing import List, Dict
from fastapi import HTTPException

from app.config import settings


def setup_logging():
    """Setup logging configuration"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'app.log')),
            logging.StreamHandler()
        ]
    )


def verify_api_key(api_key: str):
    """Verify API key"""
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def chunk_text(text_data: Dict, chunk_size: int = 512, overlap: int = 50) -> List[Dict]:
    """Chunk text from pages into smaller segments"""
    chunks = []

    for page_data in text_data.get('pages', []):
        page_num = page_data['page']
        text = page_data['text']

        # Split into sentences (simple split by periods)
        sentences = text.split('. ')

        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())

            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'text': '. '.join(current_chunk) + '.',
                    'page': page_num
                })

                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Add remaining chunk
        if current_chunk:
            chunks.append({
                'text': '. '.join(current_chunk) + '.',
                'page': page_num
            })

    return chunks