#!/bin/bash
# Magic Storybook Setup - Supports both Local and Server modes
# The setup curl command to run on the Pis
#curl -fsSL https://raw.githubusercontent.com/mikestringer/storybook-setup/main/setup.sh | bash
set -e

# ===== CONFIGURATION =====
# Set this to "local" or "server"
INSTALL_MODE="local"  # Change to "server" to skip local Ollama install

# Server settings (only used if INSTALL_MODE="server")
OLLAMA_SERVER="http://192.168.1.100:11434"  # This needs Kelly's server IP

# Model settings
#MODEL="llama3.2:3b"  # Works for both local and server modes
MODEL_LOCAL="gemma2:2b"     # Faster model for local RPi
MODEL_SERVER="llama3.1:70b" # Better model for school server
MODEL="${MODEL_LOCAL}"       # Default to local model


REPO_USER="mikestringer"  # github username e.g. https://github.com/mikestringer
REPO_NAME="storybook-setup"
# ========================

echo "=========================================="
echo "Magic Storybook Setup"
echo "Mode: ${INSTALL_MODE^^}"
echo "=========================================="

# Update system
echo "📦 [1/5] Updating system..."
#sudo apt update && sudo apt upgrade -y
export DEBIAN_FRONTEND=noninteractive
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "📦 [2/5] Installing dependencies..."
#sudo apt install -y python3-pip python3-venv git
sudo apt install -y python3-pip python3-venv git portaudio19-dev flac

# Install Ollama locally if in local mode
if [ "$INSTALL_MODE" = "local" ]; then
    echo "📦 [3/5] Installing Ollama locally..."
    curl -fsSL https://ollama.com/install.sh | sh
    
    echo "⚙️  Starting Ollama service..."
    sudo systemctl enable ollama
    sudo systemctl start ollama
    sleep 10
    
    echo "📥 Downloading AI model: ${MODEL}"
    echo "This will take 5-10 minutes..."
    ollama pull $MODEL
    ollama list
    
    OLLAMA_URL="http://localhost:11434"
else
    echo "📦 [3/5] Skipping local Ollama (using server mode)..."
    OLLAMA_URL="$OLLAMA_SERVER"
fi

# Create project directory
echo "📁 [4/5] Setting up project..."
mkdir -p /home/pi/storybook
cd /home/pi/storybook

# Download files from Bitbucket, now Github
# Download files from GitHub
echo "⬇️  Downloading project files..."
BASE_URL="https://raw.githubusercontent.com/${REPO_USER}/${REPO_NAME}/main"

curl -fsSL ${BASE_URL}/storybook.py -o storybook.py
curl -fsSL ${BASE_URL}/storybook_console.py -o storybook_console.py
curl -fsSL ${BASE_URL}/storybook_ui.py -o storybook_ui.py
curl -fsSL ${BASE_URL}/config.py -o config.py
curl -fsSL ${BASE_URL}/requirements.txt -o requirements.txt
curl -fsSL ${BASE_URL}/switch_mode.sh -o switch_mode.sh
curl -fsSL ${BASE_URL}/generate_assets.py -o generate_assets.py

# Make scripts executable
chmod +x storybook.py
chmod +x storybook_console.py
chmod +x storybook_ui.py
chmod +x switch_mode.sh

# Generate image assets for UI
echo "🎨 Generating UI assets..."
python3 generate_assets.py

# Configure for the selected mode
sed -i "s|MODE = .*|MODE = \"${INSTALL_MODE}\"|" config.py
sed -i "s|OLLAMA_SERVER = .*|OLLAMA_SERVER = \"${OLLAMA_URL}\"|" config.py
sed -i "s|MODEL = .*|MODEL = \"${MODEL}\"|" config.py

chmod +x switch_mode.sh

# Set up Python environment
echo "🐍 [5/5] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

chmod +x storybook.py

# Test the installation
echo ""
echo "🧪 Testing installation..."
python3 storybook.py --test

# Create systemd service
echo "⚙️  Creating auto-start service..."
sudo tee /etc/systemd/system/storybook.service > /dev/null << 'EOF'
[Unit]
Description=Magic Storybook
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/storybook
ExecStart=/home/pi/storybook/venv/bin/python /home/pi/storybook/storybook.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable storybook.service

# Create display rotation script (for Pi 4 with touchscreen)
echo "⚙️  Configuring display rotation..."
cat > /home/pi/rotate-display.sh << 'ROTATE_EOF'
#!/bin/bash
sleep 5
DISPLAY=:0 xrandr --output HDMI-1 --rotate right
DISPLAY=:0 xinput set-prop "QDTECH̐MPI700 MPI7002" "Coordinate Transformation Matrix" 0 1 0 -1 0 1 0 0 1
ROTATE_EOF

chmod +x /home/pi/rotate-display.sh

# Create autostart entry
mkdir -p /home/pi/.config/autostart
cat > /home/pi/.config/autostart/rotate.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Name=Rotate Display
Exec=/home/pi/rotate-display.sh
DESKTOP_EOF

echo "✅ Display rotation configured"

echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Mode: ${INSTALL_MODE^^}"
echo "Server: ${OLLAMA_URL}"
echo "Model: ${MODEL}"
echo ""
echo "To switch modes later:"
echo "  cd /home/pi/storybook"
echo "  ./switch_mode.sh local    # Use local Ollama"
echo "  ./switch_mode.sh server   # Use network server"
echo ""
echo "Commands:"
echo "  Start: sudo systemctl start storybook"
echo "  Status: sudo systemctl status storybook"
echo "  Logs: sudo journalctl -u storybook -f"
echo ""
