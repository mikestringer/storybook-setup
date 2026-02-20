#!/bin/bash
# Ollama Server Setup for Magic Storybook
# Run this once on your server to set up Ollama for network access
# The setup curl command to run from the server:
# curl -fsSL https://raw.githubusercontent.com/mikestringer/storybook-setup/main/ollama-server-setup.sh | bash

set -e

# ===== CONFIGURATION =====
MODEL="llama3.1:70b"  # Best storytelling model
OLLAMA_PORT="11434"
# =========================

echo "=========================================="
echo "Ollama Server Setup"
echo "=========================================="
echo "Port: ${OLLAMA_PORT}"
echo ""

# Update system
echo "📦 [1/5] Updating system..."
export DEBIAN_FRONTEND=noninteractive
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 [2/5] Installing dependencies..."
sudo apt install -y curl zstd

# Install Ollama
echo "📦 [3/5] Installing Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama already installed"
else
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Configure Ollama to listen on all network interfaces
echo "⚙️  [4/5] Configuring Ollama for network access..."
sudo mkdir -p /etc/systemd/system/ollama.service.d

sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF

# Reload systemd and restart Ollama
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl restart ollama

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 5

# Pull the model
echo "📥 [5/5] Downloading model: ${MODEL}"
echo "This may take 15-30 minutes for the 70b model..."
ollama pull ${MODEL}

echo "✅ Model downloaded!"
ollama list

echo ""
echo "=========================================="
echo "✅ Ollama Server Setup Complete!"
echo "=========================================="
echo ""
echo "Server is now accessible at:"
echo "  http://$(hostname -I | awk '{print $1}'):${OLLAMA_PORT}"
echo ""
echo "Model loaded: ${MODEL}"
echo ""
echo "To control the service:"
echo "  Start:   sudo systemctl start ollama"
echo "  Stop:    sudo systemctl stop ollama"
echo "  Status:  sudo systemctl status ollama"
echo ""
echo "To test from a storybook RPi:"
echo "  curl http://$(hostname -I | awk '{print $1}'):${OLLAMA_PORT}/api/tags"
echo ""
