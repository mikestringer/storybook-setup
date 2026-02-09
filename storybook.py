#!/usr/bin/env python3
"""
Magic Storybook - Main Application
Supports both local and server modes
"""

import sys
import time
import requests
from config import *

def check_connection():
    """
    Check if we can connect to Ollama (local or server)
    """
    ollama_url = get_ollama_url()
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def generate_story(prompt):
    """
    Generate a story using Ollama (local or server based on config)
    """
    ollama_url = get_ollama_url()
    
    print(f"🤖 Mode: {get_mode_description()}")
    print(f"🤖 Generating story about: {prompt}")
    
    try:
        full_prompt = (
            f"Tell a short, imaginative story for children about {prompt}. "
            f"Keep it under {MAX_STORY_LENGTH} words. "
            f"Make it fun and age-appropriate for kids ages 5-10."
        )
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": MODEL,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": TEMPERATURE,
                            "top_p": TOP_P,
                            "num_predict": NUM_PREDICT,
                            "num_ctx": NUM_CTX
                        }
                    },
                    timeout=CONNECTION_TIMEOUT
                )
                
                response.raise_for_status()
                story = response.json()['response']
                print("✅ Story generated!")
                return story.strip()
                
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    print(f"⏳ Timeout, retrying ({attempt + 1}/{MAX_RETRIES})...")
                    time.sleep(2)
                else:
                    raise
            except requests.exceptions.ConnectionError:
                if MODE == "server":
                    return (
                        "The magic book can't reach the story server right now. "
                        "Are we connected to the school network?"
                    )
                else:
                    return (
                        "The magic book's storyteller is sleeping. "
                        "Please wake it up and try again!"
                    )
    
    except Exception as e:
        print(f"❌ Error: {e}")
        if MODE == "server":
            return "The story server seems to be having trouble. Try again in a moment!"
        else:
            return "The magic had a little hiccup. Try again!"

def test_installation():
    """
    Test that everything is working in current mode
    """
    print("\n" + "="*60)
    print("TESTING MAGIC STORYBOOK")
    print("="*60 + "\n")
    
    print(f"Current mode: {get_mode_description()}\n")
    
    # Test 1: Check connection
    print("Test 1: Checking Ollama connection...")
    ollama_url = get_ollama_url()
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"✅ Connected to Ollama at {ollama_url}")
            models = response.json().get('models', [])
            print(f"   Available models: {[m['name'] for m in models]}")
            
            # Check if our model is available
            model_names = [m['name'] for m in models]
            if MODEL in model_names:
                print(f"✅ Model '{MODEL}' is ready")
            else:
                print(f"⚠️  Model '{MODEL}' not found!")
                print(f"   Run: ollama pull {MODEL}")
                return False
        else:
            print("❌ Ollama is not responding correctly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        if MODE == "server":
            print(f"   Are you connected to the network?")
            print(f"   Can you reach {OLLAMA_SERVER}?")
        else:
            print(f"   Is Ollama running? Try: sudo systemctl start ollama")
        return False
    
    # Test 2: Generate a test story
    print("\nTest 2: Generating test story...")
    if MODE == "local":
        print("(This may take 10-30 seconds on RPi 5)")
    else:
        print("(This should be faster on server)")
    print()
    
    start_time = time.time()
    story = generate_story("a brave little robot")
    elapsed = time.time() - start_time
    
    print(f"\n--- Generated Story ({elapsed:.1f} seconds) ---")
    print(story)
    print("-" * 60)
    
    if len(story) > 50:
        print(f"\n✅ Story generation successful! ({len(story.split())} words)")
    else:
        print("\n⚠️  Story seems too short, check configuration")
    
    print(f"\n⏱️  Generation time: {elapsed:.1f} seconds")
    
    if MODE == "local" and elapsed > 30:
        print("   ⚠️  This is slow - consider switching to server mode at school")
        print("   or using a smaller model like gemma2:2b")
    
    return True

def main():
    """
    Main application loop
    """
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_installation()
        return
    
    print("🎪 Magic Storybook Starting...")
    print(f"📚 Mode: {get_mode_description()}")
    print(f"📚 Model: {MODEL}")
    
    # Check connection at startup
    if not check_connection():
        print("\n❌ Cannot connect to Ollama!")
        if MODE == "server":
            print("   Not on school network? Switch to local mode:")
            print("   ./switch_mode.sh local")
        else:
            print("   Is Ollama running?")
            print("   sudo systemctl start ollama")
        return
    
    print("\n✅ Connection OK")
    print("\n⚠️  Hardware integration not yet implemented!")
    print("This is a template for you to customize.\n")
    
    # TODO: Add your hardware integration here
    
    print("Ready for stories! (Press Ctrl+C to exit)\n")
    
    try:
        test_prompts = [
            "a dragon who loves to bake cookies",
            "a friendly ghost in a library",
            "a robot learning to dance",
            "a magical garden that grows overnight"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n{'='*60}")
            print(f"Story {i}: {prompt}")
            print('='*60)
            
            story = generate_story(prompt)
            print(f"\n{story}\n")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n👋 Storybook shutting down...")

if __name__ == "__main__":
    main()
