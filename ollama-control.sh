#!/bin/bash
# Control Ollama Server
# Usage: ./ollama-control.sh [enable|disable|status]'
# Download (not run) the file command NOTE the -o 
#curl -fsSL https://raw.githubusercontent.com/mikestringer/storybook-setup/main/ollama-control.sh -o ollama-control.sh


set -e

ACTION=$1
OLLAMA_PORT="11434"

if [ -z "$ACTION" ]; then
    echo "Usage: $0 [enable|disable|status]"
    echo ""
    echo "Commands:"
    echo "  enable  - Start Ollama service"
    echo "  disable - Stop Ollama service"
    echo "  status  - Show current status"
    exit 1
fi

case "$ACTION" in
    enable)
        echo "🟢 Starting Ollama service..."
        sudo systemctl start ollama
        echo "✅ Ollama is now running on port ${OLLAMA_PORT}"
        sudo systemctl status ollama --no-pager -l
        ;;
    
    disable)
        echo "🔴 Stopping Ollama service..."
        sudo systemctl stop ollama
        echo "✅ Ollama service stopped"
        ;;
    
    status)
        echo "=========================================="
        echo "Ollama Service Status:"
        echo "=========================================="
        sudo systemctl status ollama --no-pager -l
        echo ""
        echo "=========================================="
        echo "Connection Test:"
        echo "=========================================="
        if systemctl is-active --quiet ollama; then
            echo "✅ Ollama is running"
            SERVER_IP=$(hostname -I | awk '{print $1}')
            echo "Test URL: http://${SERVER_IP}:${OLLAMA_PORT}/api/tags"
            echo ""
            echo "Testing connection..."
            curl -s http://localhost:${OLLAMA_PORT}/api/tags > /dev/null && echo "✅ Local connection works" || echo "❌ Local connection failed"
        else
            echo "❌ Ollama is stopped"
        fi
        ;;
    
    *)
        echo "Error: Unknown command '$ACTION'"
        echo "Use: enable, disable, or status"
        exit 1
        ;;
esac
