#!/bin/bash
set -e

VERSION="1.0.0"
ARCH="amd64"
PACKAGE_NAME="edge-rag-mvp"
BUILD_DIR="build/${PACKAGE_NAME}_${VERSION}_${ARCH}"

echo "Creating Debian package for Edge RAG MVP v${VERSION}"

# Create directory structure
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/edge-rag-mvp"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/etc/systemd/system"

# Copy application files
cp -r app sdk webui tests scripts requirements.txt .env.example "$BUILD_DIR/opt/edge-rag-mvp/"

# Create control file
cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Your Name <your.email@example.com>
Description: Edge RAG MVP - On-Device Document Q&A System
 A complete RAG system that runs locally on 8GB RAM devices.
 Features OCR, embeddings, FAISS indexing, and quantized LLM inference.
Depends: python3.10, python3-pip, tesseract-ocr, poppler-utils
EOF

# Create postinst script
cat > "$BUILD_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "Setting up Edge RAG MVP..."

cd /opt/edge-rag-mvp
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Edge RAG MVP installed successfully!"
echo "Run 'edge-rag-mvp start' to begin"
EOF

chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# Create launch script
cat > "$BUILD_DIR/usr/bin/edge-rag-mvp" << 'EOF'
#!/bin/bash

case "$1" in
    start)
        cd /opt/edge-rag-mvp
        source venv/bin/activate
        uvicorn app.main:app --host 0.0.0.0 --port 8000
        ;;
    stop)
        pkill -f "uvicorn app.main:app"
        ;;
    *)
        echo "Usage: edge-rag-mvp {start|stop}"
        exit 1
        ;;
esac
EOF

chmod 755 "$BUILD_DIR/usr/bin/edge-rag-mvp"

# Build package
dpkg-deb --build "$BUILD_DIR"

echo "Package created: build/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "To install:"
echo "sudo dpkg -i build/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"