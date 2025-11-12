# ============================================================================
# FILE: app/llm_runner.py
# LLM inference using Groq API (NO llama_cpp import)
# ============================================================================

import os
import logging
from typing import Optional
from groq import Groq

from app.config import settings

logger = logging.getLogger(__name__)


class LLMRunner:
    def __init__(self):
        if settings.USE_GROQ:
            self._init_groq()
        else:
            self._init_local_llm()

    def _init_groq(self):
        """Initialize Groq API client"""
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not set. Please set it in .env file or environment variables."
            )

        logger.info(f"Initializing Groq API with model: {settings.GROQ_MODEL}")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.use_groq = True
        logger.info("Groq API client initialized successfully")

    def _init_local_llm(self):
        """Initialize local LLM (not supported in Docker)"""
        raise NotImplementedError(
            "Local LLM not supported in Docker build. Please set USE_GROQ=true in .env file. "
            "For local LLM support, use native Python installation instead of Docker."
        )

    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using RAG context"""

        if self.use_groq:
            return self._generate_with_groq(query, context)
        else:
            raise NotImplementedError("Local LLM not available")

    def _generate_with_groq(self, query: str, context: str) -> str:
        """Generate answer using Groq API"""

        # Build messages for chat completion
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that answers questions based on provided context. "
                           "If the answer is not in the context, say 'I don't have enough information to answer this question.'"
            },
            {
                "role": "user",
                "content": f"""Context:
{context}

Question: {query}

Please provide a clear and concise answer based on the context above."""
            }
        ]

        try:
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS,
                top_p=1,
                stream=False
            )

            # Extract answer
            answer = chat_completion.choices[0].message.content.strip()
            return answer

        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise Exception(f"Failed to generate answer: {str(e)}")