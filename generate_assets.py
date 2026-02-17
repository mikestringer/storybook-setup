#!/usr/bin/env python3
"""
Generate image assets for Magic Storybook UI
Creates all necessary images programmatically
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Screen dimensions (rotated for landscape book mode)
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 1024

# Output directory
ASSETS_DIR = "images"

# Colors
PAPER_COLOR = (255, 250, 240)  # Warm off-white
PAPER_TEXTURE_COLOR = (245, 240, 230)
BACKGROUND_COLOR = (240, 235, 220)
BUTTON_COLOR = (200, 150, 100)  # Warm brown
BUTTON_HOVER = (220, 170, 120)
BUTTON_TEXT = (255, 255, 255)
LOADING_BG = (50, 50, 70)  # Dark blue-gray
LOADING_TEXT = (200, 200, 220)

def create_directory():
    """Create images directory if it doesn't exist"""
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
    print(f"✅ Created {ASSETS_DIR}/ directory")

def create_welcome_image():
    """Create welcome screen"""
    img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Try to load a nice font, fallback to default
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 80)
        subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 40)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Draw title
    title = "Magic Storybook"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = bbox[2] - bbox[0]
    title_height = bbox[3] - bbox[1]
    title_x = (SCREEN_WIDTH - title_width) // 2
    title_y = SCREEN_HEIGHT // 3
    
    # Add shadow
    draw.text((title_x + 3, title_y + 3), title, fill=(100, 100, 100), font=title_font)
    draw.text((title_x, title_y), title, fill=(50, 50, 100), font=title_font)
    
    # Draw subtitle
    subtitle = "Powered by AI Storytelling"
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = bbox[2] - bbox[0]
    subtitle_x = (SCREEN_WIDTH - subtitle_width) // 2
    subtitle_y = title_y + title_height + 40
    draw.text((subtitle_x, subtitle_y), subtitle, fill=(100, 100, 100), font=subtitle_font)
    
    # Add decorative elements (simple book icon)
    book_width = 200
    book_height = 150
    book_x = (SCREEN_WIDTH - book_width) // 2
    book_y = SCREEN_HEIGHT - 250
    
    # Book pages
    draw.rectangle([book_x, book_y, book_x + book_width, book_y + book_height], 
                   fill=(200, 180, 160), outline=(150, 130, 110), width=3)
    draw.line([book_x + book_width // 2, book_y, book_x + book_width // 2, book_y + book_height], 
              fill=(150, 130, 110), width=3)
    
    img.save(f"{ASSETS_DIR}/welcome.png")
    print("✅ Created welcome.png")

def create_paper_background():
    """Create paper texture background"""
    img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), PAPER_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Add subtle texture with random dots
    import random
    for _ in range(5000):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        color_variation = random.randint(-10, 10)
        color = tuple(max(0, min(255, c + color_variation)) for c in PAPER_TEXTURE_COLOR)
        draw.point((x, y), fill=color)
    
    # Apply slight blur for texture
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Add subtle vignette
    overlay = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    for i in range(200):
        alpha = int(i * 0.3)
        overlay_draw.rectangle([i, i, SCREEN_WIDTH - i, SCREEN_HEIGHT - i], 
                              outline=(0, 0, 0, alpha))
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    img.save(f"{ASSETS_DIR}/paper_background.png")
    print("✅ Created paper_background.png")

def create_loading_image():
    """Create loading screen"""
    img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), LOADING_BG)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text = "Creating Your Story..."
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (SCREEN_WIDTH - text_width) // 2
    text_y = SCREEN_HEIGHT // 2 - 50
    
    draw.text((text_x, text_y), text, fill=LOADING_TEXT, font=font)
    
    # Add spinning circles
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2 + 80
    
    for i in range(8):
        angle = i * 45
        import math
        x = center_x + int(60 * math.cos(math.radians(angle)))
        y = center_y + int(60 * math.sin(math.radians(angle)))
        alpha = 255 - (i * 30)
        draw.ellipse([x - 15, y - 15, x + 15, y + 15], 
                     fill=(200, 200, 220, alpha))
    
    img.save(f"{ASSETS_DIR}/loading.png")
    print("✅ Created loading.png")

def create_button(text, filename):
    """Create a rounded button with text"""
    button_width = 200
    button_height = 80
    
    # Create button with alpha channel for rounded corners
    img = Image.new('RGBA', (button_width, button_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle
    radius = 15
    draw.rounded_rectangle([0, 0, button_width, button_height], 
                          radius=radius, fill=BUTTON_COLOR)
    
    # Add subtle shadow/3D effect
    draw.rounded_rectangle([2, 2, button_width - 2, button_height - 2], 
                          radius=radius, outline=(255, 255, 255, 100), width=2)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Center text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (button_width - text_width) // 2
    text_y = (button_height - text_height) // 2 - 5
    
    # Text with shadow
    draw.text((text_x + 2, text_y + 2), text, fill=(0, 0, 0, 100), font=font)
    draw.text((text_x, text_y), text, fill=BUTTON_TEXT, font=font)
    
    img.save(f"{ASSETS_DIR}/{filename}")
    print(f"✅ Created {filename}")

def main():
    print("========================================")
    print("Generating Storybook UI Assets")
    print("========================================\n")
    
    create_directory()
    create_welcome_image()
    create_paper_background()
    create_loading_image()
    create_button("◀ Back", "button_back.png")
    create_button("Next ▶", "button_next.png")
    create_button("✨ New", "button_new.png")
    
    print("\n========================================")
    print("✅ All assets created successfully!")
    print("========================================")
    print(f"Assets saved to: {ASSETS_DIR}/")

if __name__ == "__main__":
    main()
