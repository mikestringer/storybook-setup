#!/bin/bash
# Control Ollama Server Access
# Usage: ./ollama-control.sh [enable|disable|status]

set -e

ACTION=$1
OLLAMA_PORT="11434"

if [ -z "$ACTION" ]; then
    echo "Usage: $0 [enable|disable|status]"
    echo ""
    echo "Commands:"
    echo "  enable  - Start Ollama and allow network access"
    echo "  disable - Stop Ollama and block network access"
    echo "  status  - Show current status"
    exit 1
fi

case "$ACTION" in
    enable)
        echo "🟢 Enabling Ollama access..."
        sudo systemctl start ollama
        sudo ufw allow ${OLLAMA_PORT}/tcp
        echo "✅ Ollama is now accessible on port ${OLLAMA_PORT}"
        sudo systemctl status ollama --no-pager -l
        ;;
    
    disable)
        echo "🔴 Disabling Ollama access..."
        sudo systemctl stop ollama
        sudo ufw deny ${OLLAMA_PORT}/tcp
        echo "✅ Ollama access disabled"
        ;;
    
    status)
        echo "=========================================="
        echo "Ollama Service Status:"
        echo "=========================================="
        sudo systemctl status ollama --no-pager -l
        echo ""
        echo "=========================================="
        echo "Firewall Status (port ${OLLAMA_PORT}):"
        echo "=========================================="
        sudo ufw status | grep ${OLLAMA_PORT} || echo "No firewall rules for port ${OLLAMA_PORT}"
        echo ""
        echo "=========================================="
        echo "Quick Test:"
        echo "=========================================="
        if systemctl is-active --quiet ollama; then
            echo "✅ Ollama is running"
            echo "Test URL: http://$(hostname -I | awk '{print $1}'):${OLLAMA_PORT}/api/tags"
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
