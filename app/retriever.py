import os
import numpy as np
import faiss
import json
from typing import List, Dict
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class FAISSRetriever:
    def __init__(self):
        self.index = None
        self.metadata = []
        self.index_path = os.path.join(settings.FAISS_INDEX_PATH, "index.faiss")
        self.metadata_path = os.path.join(settings.FAISS_INDEX_PATH, "metadata.json")

        # Try to load existing index
        self.load_index()

    def build_index(self, embeddings: np.ndarray, metadata: List[Dict]):
        """Build FAISS index with disk-backed storage"""
        if len(embeddings) == 0:
            raise ValueError("No embeddings provided")

        dimension = embeddings.shape[1]
        logger.info(f"Building FAISS index with {len(embeddings)} vectors, dim={dimension}")

        # Use IndexFlatL2 for simplicity and accuracy
        # For larger datasets, consider IndexIVFFlat with mmap
        self.index = faiss.IndexFlatL2(dimension)

        # Add vectors to index
        self.index.add(embeddings.astype('float32'))

        # Store metadata
        self.metadata = metadata

        # Save to disk
        self.save_index()

        logger.info(f"Index built with {self.index.ntotal} vectors")

    def save_index(self):
        """Save index and metadata to disk"""
        faiss.write_index(self.index, self.index_path)

        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(f"Index saved to {self.index_path}")

    def load_index(self):
        """Load index from disk if exists"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)

                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)

                logger.info(f"Loaded index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
                self.index = None
                self.metadata = []

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        if self.index is None or self.index.ntotal == 0:
            raise ValueError("Index is empty. Build index first.")

        # Reshape query embedding
        query_embedding = query_embedding.reshape(1, -1).astype('float32')

        # Search
        distances, indices = self.index.search(query_embedding, top_k)

        # Prepare results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.metadata):
                metadata = self.metadata[idx]

                # Get original text from metadata
                doc_id = metadata['doc_id']
                chunk_id = metadata['chunk_id']

                # Load document to get chunk text
                from app.ingestion import DocumentIngestion
                ingest = DocumentIngestion()
                doc = ingest.get_document(doc_id)

                if doc and chunk_id < len(doc['chunks']):
                    chunk_text = doc['chunks'][chunk_id]['text']
                else:
                    chunk_text = ""

                results.append({
                    'text': chunk_text,
                    'metadata': metadata,
                    'score': 1.0 / (1.0 + float(dist))  # Convert L2 distance to similarity score
                })

        return results

    def get_index_size_mb(self) -> float:
        """Get index file size in MB"""
        if os.path.exists(self.index_path):
            size_bytes = os.path.getsize(self.index_path)
            return size_bytes / (1024 * 1024)
        return 0.0