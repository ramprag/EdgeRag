# ============================================================================
# Dockerfile - OPTIMIZED FOR FAST BUILDS (5-10 minutes max)
# ============================================================================

FROM python:3.10-slim

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Upgrade pip first (faster downloads)
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Install packages in stages for better caching and progress visibility
# Stage 1: Install torch first (biggest package ~100MB)
RUN echo "Installing PyTorch (this may take 5-7 minutes)..." && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.2+cpu

# Stage 2: Install sentence-transformers (downloads ~200MB)
RUN echo "Installing sentence-transformers..." && \
    pip install --no-cache-dir sentence-transformers==2.3.1

# Stage 3: Install remaining packages (fast)
RUN echo "Installing remaining packages..." && \
    pip install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    python-multipart==0.0.6 \
    aiofiles==23.2.1 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0 \
    faiss-cpu==1.7.4 \
    transformers==4.36.2 \
    pytesseract==0.3.10 \
    pdfplumber==0.10.3 \
    Pillow==10.2.0 \
    pdf2image==1.16.3 \
    groq==0.4.2 \
    python-dotenv==1.0.0 \
    httpx==0.26.0 \
    tqdm==4.66.1 \
    numpy==1.24.3 \
    requests==2.31.0

# Copy application code
COPY app/ ./app/
COPY sdk/ ./sdk/
COPY webui/ ./webui/

# Create directories
RUN mkdir -p data/uploads data/processed data/faiss_index logs

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]