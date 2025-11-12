from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import os
import time
import logging

from app.config import settings
from app.models import (
    UploadResponse, BuildIndexResponse, QueryRequest,
    QueryResponse, DocumentListResponse
)
from app.ingestion import DocumentIngestion
from app.embedding import EmbeddingManager
from app.retriever import FAISSRetriever
from app.llm_runner import LLMRunner
from app.utils import setup_logging, verify_api_key

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Edge RAG MVP",
    description="On-device RAG system with OCR, embeddings, and local LLM",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
if os.path.exists("webui"):
    app.mount("/static", StaticFiles(directory="webui/static"), name="static")

# Initialize components (lazy loading)
ingestion = None
embedding_manager = None
retriever = None
llm_runner = None


def get_ingestion():
    global ingestion
    if ingestion is None:
        ingestion = DocumentIngestion()
    return ingestion


def get_embedding_manager():
    global embedding_manager
    if embedding_manager is None:
        embedding_manager = EmbeddingManager()
    return embedding_manager


def get_retriever():
    global retriever
    if retriever is None:
        retriever = FAISSRetriever()
    return retriever


def get_llm_runner():
    global llm_runner
    if llm_runner is None:
        llm_runner = LLMRunner()
    return llm_runner


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web UI"""
    try:
        with open("webui/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Edge RAG MVP</h1><p>API is running. Access /docs for API documentation.</p>")


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
        file: UploadFile = File(...),
        x_api_key: str = Header(..., alias="X-API-Key")
):
    """Upload a PDF or image document"""
    verify_api_key(x_api_key)

    start_time = time.time()
    logger.info(f"Uploading document: {file.filename}")

    try:
        ingest = get_ingestion()
        result = await ingest.process_upload(file)

        processing_time = time.time() - start_time
        logger.info(f"Document uploaded successfully: {result['doc_id']} in {processing_time:.2f}s")

        return UploadResponse(
            doc_id=result['doc_id'],
            filename=result['filename'],
            pages=result.get('pages', 0),
            status="uploaded",
            processing_time_seconds=processing_time
        )
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/build-index", response_model=BuildIndexResponse)
async def build_index(x_api_key: str = Header(..., alias="X-API-Key")):
    """Build embeddings and FAISS index for all uploaded documents"""
    verify_api_key(x_api_key)

    start_time = time.time()
    logger.info("Building index...")

    try:
        ingest = get_ingestion()
        embed_mgr = get_embedding_manager()
        ret = get_retriever()

        # Get all processed documents
        docs = ingest.get_all_documents()
        if not docs:
            raise HTTPException(status_code=400, detail="No documents to index")

        # Extract chunks and generate embeddings
        all_chunks = []
        all_metadata = []

        for doc in docs:
            chunks = doc.get('chunks', [])
            for idx, chunk in enumerate(chunks):
                all_chunks.append(chunk['text'])
                all_metadata.append({
                    'doc_id': doc['doc_id'],
                    'filename': doc['filename'],
                    'page': chunk.get('page', 0),
                    'chunk_id': idx
                })

        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = embed_mgr.generate_embeddings(all_chunks)

        # Build FAISS index
        logger.info("Building FAISS index...")
        ret.build_index(embeddings, all_metadata)

        processing_time = time.time() - start_time
        index_size = ret.get_index_size_mb()

        logger.info(f"Index built successfully in {processing_time:.2f}s")

        return BuildIndexResponse(
            status="success",
            documents_indexed=len(docs),
            total_chunks=len(all_chunks),
            embedding_time_seconds=processing_time,
            index_size_mb=index_size
        )
    except Exception as e:
        logger.error(f"Index building failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Index building failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query(
        request: QueryRequest,
        x_api_key: str = Header(..., alias="X-API-Key")
):
    """Query the RAG system"""
    verify_api_key(x_api_key)

    start_time = time.time()
    logger.info(f"Query: {request.query}")

    try:
        embed_mgr = get_embedding_manager()
        ret = get_retriever()
        llm = get_llm_runner()

        # Generate query embedding
        query_embedding = embed_mgr.generate_embeddings([request.query])[0]

        # Retrieve relevant chunks
        retrieval_start = time.time()
        results = ret.search(query_embedding, top_k=request.top_k)
        retrieval_time = (time.time() - retrieval_start) * 1000

        # Prepare context for LLM
        context_parts = []
        sources = []

        for result in results:
            chunk_text = result['text']
            metadata = result['metadata']
            score = result['score']

            context_parts.append(f"[Source: {metadata['filename']}, Page {metadata['page']}]\n{chunk_text}")

            sources.append({
                'doc_id': metadata['doc_id'],
                'filename': metadata['filename'],
                'page': metadata['page'],
                'chunk_id': metadata['chunk_id'],
                'score': float(score),
                'text': chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
            })

        context = "\n\n".join(context_parts)

        # Generate answer with LLM
        generation_start = time.time()
        answer = llm.generate_answer(request.query, context)
        generation_time = (time.time() - generation_start) * 1000

        total_latency = (time.time() - start_time) * 1000

        logger.info(f"Query completed in {total_latency:.0f}ms")

        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            latency_ms=int(total_latency),
            retrieval_time_ms=int(retrieval_time),
            generation_time_ms=int(generation_time)
        )
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/docs-list", response_model=DocumentListResponse)
async def list_documents(x_api_key: str = Header(..., alias="X-API-Key")):
    """List all uploaded documents"""
    verify_api_key(x_api_key)

    try:
        ingest = get_ingestion()
        docs = ingest.get_all_documents()

        return DocumentListResponse(
            total=len(docs),
            documents=docs
        )
    except Exception as e:
        logger.error(f"Listing documents failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Listing documents failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}