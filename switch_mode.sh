#!/bin/bash
# Switch between local and server modes

set -e

MODE=$1
CONFIG_FILE="/home/pi/storybook/config.py"

# Server IP for network mode
SERVER_IP="192.168.1.100:11434"  # ⚠️ Update this with your school server

if [ -z "$MODE" ]; then
    echo "Usage: ./switch_mode.sh [local|server]"
    echo ""
    echo "Current mode:"
    grep "^MODE = " $CONFIG_FILE
    exit 1
fi

if [ "$MODE" != "local" ] && [ "$MODE" != "server" ]; then
    echo "Error: Mode must be 'local' or 'server'"
    exit 1
fi

echo "Switching to ${MODE^^} mode..."

# Stop the service if running
sudo systemctl stop storybook 2>/dev/null || true

# Update config file
if [ "$MODE" = "local" ]; then
    sed -i 's|MODE = .*|MODE = "local"|' $CONFIG_FILE
    sed -i "s|OLLAMA_SERVER = .*|OLLAMA_SERVER = \"http://localhost:11434\"|" $CONFIG_FILE
    
    # Make sure local Ollama is running
    sudo systemctl start ollama 2>/dev/null || true
    
    echo "✅ Switched to LOCAL mode (standalone)"
    echo "   Using: http://localhost:11434"
else
    sed -i 's|MODE = .*|MODE = "server"|' $CONFIG_FILE
    sed -i "s|OLLAMA_SERVER = .*|OLLAMA_SERVER = \"http://${SERVER_IP}\"|" $CONFIG_FILE
    
    echo "✅ Switched to SERVER mode (network)"
    echo "   Using: http://${SERVER_IP}"
    echo "   ⚠️  Make sure you're connected to the school network!"
fi

# Restart the service
sudo systemctl restart storybook 2>/dev/null || true

echo ""
echo "Test the new mode:"
echo "  cd /home/pi/storybook"
echo "  source venv/bin/activate"
echo "  python3 storybook.py --test"
