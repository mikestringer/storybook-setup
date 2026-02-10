#python Configuration for Magic Storybook
# This file is automatically updated by setup.sh and switch_mode.sh

# ===== MODE SELECTION =====
MODE = "local"  # "local" or "server" - automatically set by scripts
# ==========================

# Ollama connection settings
OLLAMA_SERVER = "http://localhost:11434"  # Automatically set based on MODE
MODEL = "llama3.2:3b"

# Story generation settings
MAX_STORY_LENGTH = 150  # words
TEMPERATURE = 0.8  # creativity (0.0-1.0)
TOP_P = 0.9
NUM_PREDICT = 300
NUM_CTX = 2048

# Hardware pins (customize for your Adafruit setup)
BUTTON_PIN = 17
LED_PIN = 18
NEOPIXEL_PIN = 12
NUM_PIXELS = 12

# Audio
ENABLE_AUDIO = False
AUDIO_DEVICE = "default"

# Connection settings
CONNECTION_TIMEOUT = 60  # seconds
MAX_RETRIES = 3

def get_ollama_url():
    """
    Returns the appropriate Ollama URL based on current mode
    """
    if MODE == "local":
        return "http://localhost:11434"
    else:
        return OLLAMA_SERVER

def get_mode_description():
    """
    Returns a human-readable description of the current mode
    """
    if MODE == "local":
        return f"Local Ollama (standalone mode)"
    else:
        return f"Network Server ({OLLAMA_SERVER})"
