#!/usr/bin/env python3
"""
Magic Storybook - Robust Pygame Touchscreen UI Version
Supports both local and server modes with voice input
"""

import sys
import os
import time
import signal
import threading
import re
import pygame
import requests
import speech_recognition as sr
from config import *

# Optional hardware (gracefully handle if not present)
try:
    import board
    import digitalio
    import neopixel
    from adafruit_led_animation.animation.pulse import Pulse
    NEOPIXEL_AVAILABLE = True
except (ImportError, NotImplementedError):
    NEOPIXEL_AVAILABLE = False
    print("⚠️  NeoPixel support not available")

try:
    from rpi_backlight import Backlight
    BACKLIGHT_AVAILABLE = True
except ImportError:
    BACKLIGHT_AVAILABLE = False
    print("⚠️  Backlight control not available")

# Base path
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGES_PATH = os.path.join(BASE_PATH, "images/")

# NeoPixel Settings (from config or defaults)
NEOPIXEL_PIN = getattr(board, f'D{NEOPIXEL_PIN}', None) if NEOPIXEL_AVAILABLE else None
NEOPIXEL_COUNT = 1
NEOPIXEL_BRIGHTNESS = 0.2
NEOPIXEL_ORDER = neopixel.GRBW if NEOPIXEL_AVAILABLE else None

# Status Colors
NEOPIXEL_LOADING_COLOR = (0, 255, 0, 0)   # Green - Loading/Dreaming
NEOPIXEL_SLEEP_COLOR = (0, 0, 0, 0)        # Off - Sleeping
NEOPIXEL_WAITING_COLOR = (255, 255, 0, 0) # Yellow - Waiting for Input
NEOPIXEL_READING_COLOR = (0, 0, 255, 0)   # Blue - Reading

# Reed Switch Settings
REED_SWITCH_PIN = board.D17 if NEOPIXEL_AVAILABLE else None
REED_SWITCH_ENABLED = False  # Set to True when reed switch is installed

# UI Settings
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 1024
ROTATION = 0  # No rotation needed - OS handles it

# Font Settings
try:
    TITLE_FONT = ("DejaVuSerif-Bold.ttf", 36)
    TEXT_FONT = ("DejaVuSerif.ttf", 22)
except:
    TITLE_FONT = (None, 36)
    TEXT_FONT = (None, 22)

TITLE_COLOR = (0, 0, 0)
TEXT_COLOR = (0, 0, 0)

# Layout Settings
PAGE_TOP_MARGIN = 20
PAGE_SIDE_MARGIN = 20
PAGE_BOTTOM_MARGIN = 20
PAGE_NAV_HEIGHT = 100
PARAGRAPH_SPACING = 20
EXTRA_LINE_SPACING = 4

# Animation Settings
WORD_DELAY = 0.05
TITLE_FADE_TIME = 0.05
TITLE_FADE_STEPS = 10
TEXT_FADE_TIME = 0.1
TEXT_FADE_STEPS = 20

# Robustness Settings
VOICE_TIMEOUT = 30  # Maximum seconds to wait for voice input
ALSA_ERROR_DELAY = 0.5  # Delay after ALSA errors before showing "listening"


class VoiceListener:
    """Voice listener using local Whisper with robustness improvements"""
    
    def __init__(self, energy_threshold=300, record_timeout=10):
        print("🎤 Initializing voice listener...")
        self._listening = False
        self._stop_listening = False
        
        # Find USB microphone automatically
        mic_list = sr.Microphone.list_microphone_names()
        usb_mic_index = None
        for i, name in enumerate(mic_list):
            if 'USB' in name.upper() or 'PNP' in name.upper():
                usb_mic_index = i
                print(f"🎤 Found USB microphone: {name}")
                break
        
        if usb_mic_index is not None:
            self.microphone = sr.Microphone(device_index=usb_mic_index)
        else:
            self.microphone = sr.Microphone()
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.pause_threshold = 1
        self.record_timeout = record_timeout
        
        print("🎤 Calibrating microphone...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone ready!")
        except Exception as e:
            print(f"⚠️  Microphone calibration warning: {e}")
    
    def listen_for_prompt(self, ready_callback=None, interrupt_flag=None):
        """Listen for a story prompt with interrupt support"""
        self._listening = True
        self._stop_listening = False
        
        # Wait for ALSA to settle before showing "listening"
        time.sleep(ALSA_ERROR_DELAY)
        
        # Call ready callback (shows "listening" indicator)
        if ready_callback and not (interrupt_flag and interrupt_flag()):
            ready_callback()
        
        with self.microphone as source:
            try:
                # Check for interrupt before listening
                if interrupt_flag and interrupt_flag():
                    self._listening = False
                    return None
                
                print("\n🎤 Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=3,
                    phrase_time_limit=self.record_timeout
                )
                
                # Check for interrupt before processing
                if interrupt_flag and interrupt_flag():
                    self._listening = False
                    return None
                
                print("🎤 Processing speech...")
                text = self.recognizer.recognize_whisper(
                    audio,
                    language="english",
                    model="base"
                )
                
                print(f"✅ You said: {text}")
                self._listening = False
                return text.strip()
                
            except sr.WaitTimeoutError:
                print("⏱️  Timeout - no speech detected")
                self._listening = False
                return None
            except sr.UnknownValueError:
                print("❌ Could not understand speech")
                self._listening = False
                return None
            except Exception as e:
                print(f"❌ Voice error: {e}")
                self._listening = False
                return None
    
    def stop_listening(self):
        """Force stop listening"""
        self._stop_listening = True
    
    def is_listening(self):
        """Check if currently listening"""
        return self._listening
    
    def cleanup(self):
        """Release microphone resources"""
        try:
            print("🎤 Releasing microphone...")
            self.microphone = None
            self.recognizer = None
            print("✅ Microphone released")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


class Button:
    """Touch button"""
    def __init__(self, x, y, image, action):
        self.x = x
        self.y = y
        self.image = image
        self.action = action
        self.width = image.get_width()
        self.height = image.get_height()
        self.visible = False
    
    def is_in_bounds(self, pos):
        x, y = pos
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def show(self, screen):
        screen.blit(self.image, (self.x, self.y))
        self.visible = True


class Storybook:
    """Main storybook UI application with robustness improvements"""
    
    def __init__(self):
        self.pages = []
        self.stories = []
        self.current_page = 0
        self.current_story = 0
        
        # Robustness flags
        self._running = True
        self._busy = False
        self._sleep_request = False
        self._loading = False
        
        # Corner tap tracking for secret exit
        self._corner_taps = []
        
        # Initialize Pygame
        os.putenv('SDL_FBDEV', '/dev/fb0')
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
        
        # Load fonts
        try:
            font_path = f"/usr/share/fonts/truetype/dejavu/{TITLE_FONT[0]}"
            self.title_font = pygame.font.Font(font_path, TITLE_FONT[1])
        except:
            self.title_font = pygame.font.Font(None, TITLE_FONT[1])
        
        try:
            font_path = f"/usr/share/fonts/truetype/dejavu/{TEXT_FONT[0]}"
            self.text_font = pygame.font.Font(font_path, TEXT_FONT[1])
        except:
            self.text_font = pygame.font.Font(None, TEXT_FONT[1])
        
        # Load images
        self.images = {}
        self._load_image('welcome', 'welcome.png')
        self._load_image('background', 'paper_background.png')
        self._load_image('loading', 'loading.png')
        
        # Create buttons
        self.buttons = {}
        button_images = {
            'back': pygame.image.load(IMAGES_PATH + 'button_back.png'),
            'next': pygame.image.load(IMAGES_PATH + 'button_next.png'),
            'new': pygame.image.load(IMAGES_PATH + 'button_new.png')
        }
        
        # Position buttons at bottom
        button_spacing = (SCREEN_WIDTH - sum(img.get_width() for img in button_images.values())) // 4
        button_y = SCREEN_HEIGHT - PAGE_NAV_HEIGHT + (PAGE_NAV_HEIGHT - button_images['back'].get_height()) // 2
        
        x_pos = button_spacing
        for name, img in button_images.items():
            action = {
                'back': self.previous_page,
                'next': self.next_page,
                'new': self.new_story
            }[name]
            self.buttons[name] = Button(x_pos, button_y, img, action)
            x_pos += img.get_width() + button_spacing
        
        # Text area
        self.text_area = {
            'x': PAGE_SIDE_MARGIN,
            'y': PAGE_TOP_MARGIN,
            'width': SCREEN_WIDTH - PAGE_SIDE_MARGIN * 2,
            'height': SCREEN_HEIGHT - PAGE_NAV_HEIGHT - PAGE_TOP_MARGIN - PAGE_BOTTOM_MARGIN
        }
        
        # Initialize hardware
        if NEOPIXEL_AVAILABLE and NEOPIXEL_PIN:
            try:
                self.pixels = neopixel.NeoPixel(
                    NEOPIXEL_PIN,
                    NEOPIXEL_COUNT,
                    brightness=NEOPIXEL_BRIGHTNESS,
                    pixel_order=NEOPIXEL_ORDER,
                    auto_write=False
                )
                self._set_status_color(NEOPIXEL_LOADING_COLOR)
                
                # Start loading animation thread
                self._loading_thread = threading.Thread(target=self._handle_loading_animation)
                self._loading_thread.daemon = True
                self._loading_thread.start()
            except Exception as e:
                print(f"⚠️  NeoPixel init failed: {e}")
                self.pixels = None
        else:
            self.pixels = None
        
        if BACKLIGHT_AVAILABLE:
            try:
                self.backlight = Backlight()
            except Exception as e:
                print(f"⚠️  Backlight init failed: {e}")
                self.backlight = None
        else:
            self.backlight = None
        
        # Initialize voice listener
        try:
            self.listener = VoiceListener()
        except Exception as e:
            print(f"❌ Voice init failed: {e}")
            self.listener = None
    
    def _handle_loading_animation(self):
        """Pulse NeoPixel during loading"""
        if not self.pixels:
            return
        
        try:
            pulse = Pulse(
                self.pixels,
                speed=0.1,
                color=NEOPIXEL_LOADING_COLOR,
                period=3
            )
            
            while self._running:
                if self._loading:
                    pulse.animate()
                time.sleep(0.1)
        except:
            pass
    
    def _load_image(self, name, filename):
        """Load an image"""
        try:
            self.images[name] = pygame.image.load(IMAGES_PATH + filename)
        except Exception as e:
            print(f"⚠️  Failed to load {filename}: {e}")
    
    def _set_status_color(self, color):
        """Set NeoPixel status color"""
        if self.pixels:
            self._loading = (color == NEOPIXEL_LOADING_COLOR)
            if not self._loading:
                self.pixels.fill(color)
                self.pixels.show()
    
    def display_image(self, image_name):
        """Display a full-screen image"""
        if image_name in self.images:
            self.screen.blit(self.images[image_name], (0, 0))
            pygame.display.flip()
    
    def display_welcome(self):
        """Show welcome screen"""
        self.display_image('welcome')
    
    def display_loading(self):
        """Show loading screen"""
        self.display_image('loading')
        self._set_status_color(NEOPIXEL_LOADING_COLOR)
    
    def display_message(self, message):
        """Display a centered message"""
        self._busy = True
        self.screen.blit(self.images['background'], (0, 0))
        
        # Render message
        lines = self._wrap_text(message, self.title_font, self.text_area['width'])
        total_height = len(lines) * self.title_font.get_height()
        y = (SCREEN_HEIGHT - total_height) // 2
        
        for line in lines:
            text_surface = self.title_font.render(line, True, TITLE_COLOR)
            x = (SCREEN_WIDTH - text_surface.get_width()) // 2
            self.screen.blit(text_surface, (x, y))
            y += self.title_font.get_height()
        
        pygame.display.flip()
        self._busy = False
    
    def _wrap_text(self, text, font, width):
        """Wrap text to fit width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def generate_story(self, prompt):
        """Generate a story using Ollama"""
        ollama_url = get_ollama_url()
        
        full_prompt = (
            f"Tell a short, imaginative story for children about {prompt}. "
            f"Keep it under {MAX_STORY_LENGTH} words. "
            f"Make it fun and age-appropriate for kids ages 5-10. "
            f"Format: Title: [story title]\\n\\n[story text with paragraphs]"
        )
        
        try:
            # Check for interrupt before making request
            if self._sleep_request:
                return None
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": full_prompt,
                    "stream": False,
                    "keep_alive": -1,
                    "options": {
                        "temperature": TEMPERATURE,
                        "top_p": TOP_P,
                        "num_predict": NUM_PREDICT,
                        "num_ctx": NUM_CTX
                    }
                },
                timeout=CONNECTION_TIMEOUT
            )
            
            # Check for interrupt after request
            if self._sleep_request:
                return None
            
            response.raise_for_status()
            return response.json()['response'].strip()
            
        except Exception as e:
            print(f"❌ Story generation error: {e}")
            return "Title: Oops!\n\nThe magic book had a little hiccup. Let's try again!"
    
    def strip_markdown(self, text):
        """Remove markdown formatting from story text"""
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        return text.strip()
    
    def load_story(self, story_text):
        """Parse story and create pages"""
        self._busy = True
        self.pages = []
        story_text = self.strip_markdown(story_text)
        
        # Parse title and content
        if story_text.startswith("Title: "):
            parts = story_text.split("\n\n", 1)
            title = parts[0].replace("Title: ", "").strip()
            content = parts[1] if len(parts) > 1 else ""
        else:
            title = "A Story"
            content = story_text
        
        # Create first page with title
        current_page = self._create_page(title)
        y_offset = self.title_font.get_height() + PARAGRAPH_SPACING
        
        # Add content paragraphs
        paragraphs = content.split("\n\n")
        for paragraph in paragraphs:
            # Check for interrupt
            if self._sleep_request:
                self._busy = False
                return
            
            lines = self._wrap_text(paragraph, self.text_font, self.text_area['width'])
            
            for line in lines:
                text_surface = self.text_font.render(line, True, TEXT_COLOR)
                
                # Check if we need a new page
                if y_offset + text_surface.get_height() > current_page.get_height():
                    self.pages.append(current_page)
                    current_page = self._create_page()
                    y_offset = 0
                
                current_page.blit(text_surface, (0, y_offset))
                y_offset += text_surface.get_height() + EXTRA_LINE_SPACING
            
            y_offset += PARAGRAPH_SPACING
        
        self.pages.append(current_page)
        self._set_status_color(NEOPIXEL_READING_COLOR)
        self._busy = False
    
    def _create_page(self, title=None):
        """Create a new page surface using background image"""
        page_surface = pygame.Surface(
            (self.text_area['width'], self.text_area['height'])
        )
        
        # Scale background image to fit page size
        if 'background' in self.images:
            scaled_bg = pygame.transform.scale(
                self.images['background'],
                (self.text_area['width'], self.text_area['height'])
            )
            page_surface.blit(scaled_bg, (0, 0))
        else:
            page_surface.fill((255, 250, 240))
        
        if title:
            lines = self._wrap_text(title, self.title_font, self.text_area['width'])
            y = 0
            for line in lines:
                text_surface = self.title_font.render(line, True, TITLE_COLOR)
                x = (self.text_area['width'] - text_surface.get_width()) // 2
                page_surface.blit(text_surface, (x, y))
                y += self.title_font.get_height()
        
        return page_surface
    
    def display_current_page(self):
        """Display the current page"""
        self._busy = True
        
        # Draw background
        self.screen.blit(self.images['background'], (0, 0))
        
        # Draw page content
        if self.pages:
            page = self.pages[self.current_page]
            self.screen.blit(page, (self.text_area['x'], self.text_area['y']))
        
        # Draw buttons
        if self.current_page > 0 or self.current_story > 0:
            self.buttons['back'].show(self.screen)
        
        self.buttons['next'].show(self.screen)
        self.buttons['new'].show(self.screen)
        
        pygame.display.flip()
        self._busy = False
    
    def previous_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
        elif self.current_story > 0:
            self.current_story -= 1
            self.load_story(self.stories[self.current_story])
            self.current_page = len(self.pages) - 1
        
        self.display_current_page()
    
    def next_page(self):
        """Go to next page"""
        self.current_page += 1
        
        if self.current_page >= len(self.pages):
            if self.current_story < len(self.stories) - 1:
                self.current_story += 1
                self.load_story(self.stories[self.current_story])
                self.current_page = 0
            else:
                self.new_story()
                return
        
        self.display_current_page()
    
    def new_story(self):
        """Generate a new story with timeout and error handling"""
        # Prevent concurrent story generation
        if self._busy:
            return
        
        if not self.listener:
            self.display_message("Voice input not available!\n\nPlease restart the storybook.")
            time.sleep(3)
            self.display_current_page() if self.pages else self.display_welcome()
            return
        
        self._busy = True
        self.display_message("Please tell me your story idea...")
        pygame.display.flip()
        time.sleep(1)
        
        # Check for interrupt
        if self._sleep_request:
            self._busy = False
            return
        
        # Set waiting color and prepare for voice input
        def show_listening():
            """Callback when mic is ready"""
            if not self._sleep_request:
                self._set_status_color(NEOPIXEL_WAITING_COLOR)
        
        # Listen with timeout wrapper
        prompt = None
        listen_result = [None]
        listen_error = [None]
        
        def listen_thread():
            """Thread to listen with interrupt support"""
            try:
                listen_result[0] = self.listener.listen_for_prompt(
                    ready_callback=show_listening,
                    interrupt_flag=lambda: self._sleep_request
                )
            except Exception as e:
                listen_error[0] = str(e)
        
        # Start listening thread
        thread = threading.Thread(target=listen_thread)
        thread.daemon = True
        thread.start()
        
        # Wait with timeout
        thread.join(timeout=VOICE_TIMEOUT)
        
        # Check result
        if thread.is_alive():
            # Timeout - mic not responding
            print("⚠️  Voice input timeout")
            self._set_status_color(NEOPIXEL_READING_COLOR)
            self.display_message(
                "Microphone not responding.\n\n"
                "Please unplug and replug\n"
                "the USB microphone.\n\n"
                "Tap screen to continue."
            )
            self._busy = False
            
            # Wait for tap
            waiting = True
            while waiting and self._running:
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        waiting = False
                        break
                time.sleep(0.1)
            
            if self.pages:
                self.display_current_page()
            else:
                self.display_welcome()
            return
        
        # Check for errors
        if listen_error[0]:
            print(f"⚠️  Voice error: {listen_error[0]}")
            self._set_status_color(NEOPIXEL_READING_COLOR)
            self.display_message("Voice error.\n\nTap to try again.")
            self._busy = False
            
            # Wait for tap
            waiting = True
            while waiting and self._running:
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        waiting = False
                        break
                time.sleep(0.1)
            
            if self.pages:
                self.display_current_page()
            else:
                self.display_welcome()
            return
        
        # Get the prompt
        prompt = listen_result[0]
        
        # Check for interrupt
        if self._sleep_request:
            self._busy = False
            return
        
        if not prompt:
            print("No prompt detected")
            self._set_status_color(NEOPIXEL_READING_COLOR)
            self.display_message("No speech detected.\n\nTap to try again.")
            self._busy = False
            
            # Wait for tap
            waiting = True
            while waiting and self._running:
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        waiting = False
                        break
                time.sleep(0.1)
            
            if self.pages:
                self.display_current_page()
            else:
                self.display_welcome()
            return
        
        # Generate story
        self.display_loading()
        story = self.generate_story(prompt)
        
        # Check for interrupt
        if self._sleep_request or story is None:
            self._busy = False
            return
        
        # Add to stories and display
        self.stories.append(story)
        self.current_story = len(self.stories) - 1
        self.current_page = 0
        
        self.load_story(story)
        
        # Check for interrupt
        if self._sleep_request:
            self._busy = False
            return
        
        self.display_current_page()
    
    def handle_events(self):
        """Handle touch events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            
            # ESC key to exit (for testing/admin)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("ESC pressed - exiting...")
                    self._running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos
                
                # Check for secret exit (tap top-right corner 3 times)
                if x > SCREEN_WIDTH - 50 and y < 50:
                    self._corner_taps.append(time.time())
                    self._corner_taps = [t for t in self._corner_taps 
                                        if time.time() - t < 3]
                    if len(self._corner_taps) >= 3:
                        print("Corner tapped 3 times - exiting...")
                        self._running = False
                        return
                
                # Check button clicks
                for button in self.buttons.values():
                    if button.visible and button.is_in_bounds(event.pos):
                        button.action()
    
    def run(self):
        """Main loop"""
        try:
            # Show welcome
            self.display_welcome()
            time.sleep(2)
            
            # Generate first story
            if not self._sleep_request:
                self.new_story()
            
            # Main event loop
            while self._running:
                self.handle_events()
                time.sleep(0.1)
        
        finally:
            # Cleanup
            self._cleanup()
    
    def _cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        
        # Set sleep request to interrupt any running operations
        self._sleep_request = True
        
        # Stop voice listener
        if self.listener:
            if self.listener.is_listening():
                self.listener.stop_listening()
            self.listener.cleanup()
        
        # Wait for busy operations to complete
        timeout = 5
        start = time.time()
        while self._busy and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        # Turn off NeoPixels
        if self.pixels:
            self.pixels.fill((0, 0, 0, 0))
            self.pixels.show()
        
        # Turn on backlight
        if self.backlight:
            try:
                self.backlight.power = True
            except:
                pass
        
        pygame.quit()
        print("✅ Cleanup complete")


def main():
    """Entry point"""
    print("🎪 Starting Magic Storybook UI...")
    
    book = None
    
    def cleanup_handler(signum, frame):
        """Handle interrupt signals"""
        print("\n🛑 Interrupt received, cleaning up...")
        if book:
            book._sleep_request = True
            book._running = False
    
    # Register signal handlers
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    try:
        book = Storybook()
        book.run()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if book:
            book._cleanup()


if __name__ == "__main__":
    main()
