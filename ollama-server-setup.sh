#!/bin/bash
# Ollama Server Setup for Magic Storybook
# Run this once on your server to set up Ollama for network access
# The setup curl command to run from the server
# curl -fsSL https://raw.githubusercontent.com/mikestringer/storybook-setup/main/ollama-server-setup.sh | bash

set -e

# ===== CONFIGURATION =====
#MODEL="llama3.2:3b"  # Model to serve
MODEL="llama3.1:70b"  # Best story telling model to serve, may be too resource intensive
ALLOWED_NETWORK="10.110.66.0/24"  # School network range - adjust as needed
OLLAMA_PORT="11434"
# =========================

echo "=========================================="
echo "Ollama Server Setup"
echo "=========================================="
echo "Server will accept connections from: ${ALLOWED_NETWORK}"
echo "Port: ${OLLAMA_PORT}"
echo ""

# Update system
echo "📦 [1/6] Updating system..."
export DEBIAN_FRONTEND=noninteractive
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 [2/6] Installing dependencies..."
sudo apt install -y curl ufw zstd

# Install Ollama
echo "📦 [3/6] Installing Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama already installed"
else
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Configure Ollama to listen on all network interfaces
echo "⚙️  [4/6] Configuring Ollama for network access..."
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
echo "📥 [5/6] Downloading model: ${MODEL}"
echo "This may take 5-10 minutes..."
ollama pull ${MODEL}

echo "✅ Model downloaded!"
ollama list

# Configure firewall
echo "🔒 [6/6] Configuring firewall..."

# Enable UFW if not already enabled
sudo ufw --force enable

# Allow SSH (important - don't lock yourself out!)
sudo ufw allow 2222/tcp comment 'SSH'

# Allow Ollama only from school network
sudo ufw allow from ${ALLOWED_NETWORK} to any port ${OLLAMA_PORT} proto tcp comment 'Ollama for storybooks'

# Show firewall status
echo ""
echo "Firewall rules:"
sudo ufw status numbered

echo ""
echo "=========================================="
echo "✅ Ollama Server Setup Complete!"
echo "=========================================="
echo ""
echo "Server is now accessible at:"
echo "  http://$(hostname -I | awk '{print $1}'):${OLLAMA_PORT}"
echo ""
echo "Model loaded: ${MODEL}"
echo "Allowed network: ${ALLOWED_NETWORK}"
echo ""
echo "To control access later:"
echo "  Enable:  sudo systemctl start ollama && sudo ufw allow ${OLLAMA_PORT}"
echo "  Disable: sudo systemctl stop ollama && sudo ufw deny ${OLLAMA_PORT}"
echo ""
echo "To test from a storybook RPi:"
echo "  curl http://$(hostname -I | awk '{print $1}'):${OLLAMA_PORT}/api/tags"
echo ""

