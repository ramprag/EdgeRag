#!/bin/bash
set -e

SWAP_SIZE="32G"
SWAP_FILE="/swapfile"

echo "Creating ${SWAP_SIZE} swap file..."

# Check if swap already exists
if [ -f "$SWAP_FILE" ]; then
    echo "Swap file already exists. Removing old swap..."
    sudo swapoff "$SWAP_FILE" || true
    sudo rm "$SWAP_FILE"
fi

# Create swap file
echo "Allocating swap space..."
sudo fallocate -l "$SWAP_SIZE" "$SWAP_FILE"

# Set permissions
echo "Setting permissions..."
sudo chmod 600 "$SWAP_FILE"

# Make swap
echo "Making swap..."
sudo mkswap "$SWAP_FILE"

# Enable swap
echo "Enabling swap..."
sudo swapon "$SWAP_FILE"

# Make permanent
if ! grep -q "$SWAP_FILE" /etc/fstab; then
    echo "Adding swap to /etc/fstab..."
    echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab
fi

# Verify
echo ""
echo "Swap configuration:"
free -h
echo ""
echo "Swap file created successfully!"
