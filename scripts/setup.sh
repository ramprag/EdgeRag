#!/bin/bash
set -e

echo "========================================="
echo "Edge RAG MVP - Automated Setup"
echo "========================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Warning: This script is designed for Linux. Some steps may fail on other OS."
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Step 1: Updating system packages...${NC}"
sudo apt-get update

echo -e "${GREEN}Step 2: Installing system dependencies...${NC}"
sudo apt-get install -y \
    python3.10 python3.10-venv python3-pip \
    tesseract-ocr tesseract-ocr-eng \
    poppler-utils \
    git wget curl \
    build-essential cmake \
    libblas-dev liblapack-dev \
    libopenblas-dev

echo -e "${GREEN}Step 3: Checking swap space...${NC}"
SWAP_SIZE=$(free -m | grep Swap | awk '{print $2}')
if [ "$SWAP_SIZE" -lt 30000 ]; then
    echo -e "${YELLOW}Swap space is less than 30GB. Creating 32GB swap...${NC}"
    ./scripts/create_swap.sh
else
    echo -e "${GREEN}Sufficient swap space available: ${SWAP_SIZE}MB${NC}"
fi

echo -e "${GREEN}Step 4: Creating Python virtual environment...${NC}"
python3.10 -m venv venv
source venv/bin/activate

echo -e "${GREEN}Step 5: Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel

echo -e "${GREEN}Step 6: Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Install llama-cpp-python with OpenBLAS support
echo -e "${GREEN}Step 7: Installing llama-cpp-python with optimizations...${NC}"
CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" pip install llama-cpp-python==0.2.27 --force-reinstall --no-cache-dir

echo -e "${GREEN}Step 8: Creating directory structure...${NC}"
mkdir -p models data/uploads data/processed data/faiss_index logs webui/static

echo -e "${GREEN}Step 9: Setting up configuration...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env file and set your API_KEY${NC}"
fi

echo -e "${GREEN}Step 10: Downloading LLM model...${NC}"
if [ ! -f models/vicuna-7b-v1.5.Q4_0.gguf ]; then
    echo "Downloading Vicuna 7B Q4_0 model (~3.8GB)..."
    cd models
    wget https://huggingface.co/TheBloke/vicuna-7B-v1.5-GGUF/resolve/main/vicuna-7b-v1.5.Q4_0.gguf
    cd ..
    echo -e "${GREEN}Model downloaded successfully${NC}"
else
    echo -e "${GREEN}Model already exists${NC}"
fi

echo ""
echo -e "${GREEN}========================================="
echo "Setup completed successfully!"
echo "=========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file and set your API_KEY"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Start server: uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "4. Open browser: http://localhost:8000"
echo ""
echo "For more information, see README.md"