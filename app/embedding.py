import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from typing import List
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingManager:
    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")

        # Set device to CPU explicitly for 8GB RAM systems
        self.device = 'cpu'

        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=self.device
        )

        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not texts:
            return np.array([])

        logger.info(f"Generating embeddings for {len(texts)} texts...")

        # Process in batches to manage memory
        batch_size = settings.EMBEDDING_BATCH_SIZE
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            with torch.no_grad():
                embeddings = self.model.encode(
                    batch,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    normalize_embeddings=True  # L2 normalization
                )

            all_embeddings.append(embeddings)

            if (i + batch_size) % 100 == 0:
                logger.info(f"Processed {i + batch_size}/{len(texts)} texts")

        return np.vstack(all_embeddings)